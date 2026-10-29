"""Construit les tables lues par Tableau à partir des données brutes.

Sorties (data/donnees/) :
- exportations.csv : une ligne par année, pays de destination et code SH à 6 chiffres
- controles.json   : contrôles qualité (cohérence avec le total « Monde » publié)
"""
from __future__ import annotations

import gettext
import json
from pathlib import Path

import pandas as pd
import pycountry
import pycountry_convert as pcc

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "donnees"
OUT.mkdir(parents=True, exist_ok=True)

# Nomenclature SH : 9101 = boîte en métal précieux, 9102 = autres boîtes (acier, titane, céramique...)
CODES = {
    "910111": ("Montres-bracelets", "Métal précieux", "Électronique (quartz)"),
    "910112": ("Montres-bracelets", "Métal précieux", "Électronique (quartz)"),
    "910119": ("Montres-bracelets", "Métal précieux", "Électronique (quartz)"),
    "910121": ("Montres-bracelets", "Métal précieux", "Mécanique automatique"),
    "910129": ("Montres-bracelets", "Métal précieux", "Mécanique à remontage manuel"),
    "910191": ("Montres de poche et autres", "Métal précieux", "Électronique (quartz)"),
    "910199": ("Montres de poche et autres", "Métal précieux", "Mécanique à remontage manuel"),
    "910211": ("Montres-bracelets", "Acier et autres", "Électronique (quartz)"),
    "910212": ("Montres-bracelets", "Acier et autres", "Électronique (quartz)"),
    "910219": ("Montres-bracelets", "Acier et autres", "Électronique (quartz)"),
    "910221": ("Montres-bracelets", "Acier et autres", "Mécanique automatique"),
    "910229": ("Montres-bracelets", "Acier et autres", "Mécanique à remontage manuel"),
    "910291": ("Montres de poche et autres", "Acier et autres", "Électronique (quartz)"),
    "910299": ("Montres de poche et autres", "Acier et autres", "Mécanique à remontage manuel"),
}

FR = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"])
NOMS_FR = {"USA": "États-Unis", "KOR": "Corée du Sud", "TWN": "Taïwan", "HKG": "Hong Kong", "GBR": "Royaume-Uni",
           "ARE": "Émirats arabes unis", "RUS": "Russie", "CZE": "Tchéquie", "VNM": "Vietnam", "IRN": "Iran",
           "MAC": "Macao", "SYR": "Syrie", "TUR": "Turquie", "BOL": "Bolivie", "VEN": "Venezuela", "TZA": "Tanzanie",
           "MDA": "Moldavie", "LAO": "Laos", "PRK": "Corée du Nord", "BRN": "Brunei", "CIV": "Côte d'Ivoire"}
NOMS_EN = {"KOR": "South Korea", "TWN": "Taiwan", "HKG": "Hong Kong", "RUS": "Russia", "TUR": "Turkey",
           "IRN": "Iran", "VNM": "Vietnam", "SYR": "Syria", "BOL": "Bolivia", "VEN": "Venezuela", "TZA": "Tanzania",
           "MDA": "Moldova", "LAO": "Laos", "PRK": "North Korea", "BRN": "Brunei", "CZE": "Czech Republic", "MAC": "Macau"}
MOYEN_ORIENT = {"ARE", "SAU", "QAT", "KWT", "BHR", "OMN", "ISR", "JOR", "LBN", "IRQ", "IRN", "SYR", "YEM", "PSE"}
CONTINENTS = {"AF": "Afrique", "AS": "Asie", "EU": "Europe", "OC": "Océanie", "SA": "Amérique latine", "NA": "Amérique latine"}


def pays(iso3: str) -> tuple[str, str, str]:
    c = pycountry.countries.get(alpha_3=iso3)
    if c is None:
        return iso3, iso3, "Autres"
    fr = NOMS_FR.get(iso3, FR.gettext(c.name))
    en = NOMS_EN.get(iso3, getattr(c, "common_name", c.name))
    autres = {"VAT": "Europe", "TLS": "Asie", "SXM": "Amérique latine", "UMI": "Océanie", "ATF": "Afrique", "HMD": "Océanie"}
    if iso3 in autres:
        reg = autres[iso3]
    elif iso3 in MOYEN_ORIENT:
        reg = "Moyen-Orient"
    elif iso3 in ("USA", "CAN"):
        reg = "Amérique du Nord"
    elif iso3 == "TWN":
        reg = "Asie"
    else:
        try:
            reg = CONTINENTS[pcc.country_alpha2_to_continent_code(c.alpha_2)]
        except KeyError:
            reg = "Autres"
    return fr, en, reg


def charger(dossier: str) -> list[dict]:
    return [r for f in sorted((RAW / dossier).glob("*.json")) for r in json.loads(f.read_text(encoding="utf-8"))]


def taux_chf() -> pd.DataFrame:
    """Cours moyen mensuel CHF pour 1 USD (BNS, cube devkum)."""
    lines = (RAW / "snb_devkum.csv").read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.replace('"', "").startswith("Date;"))
    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(lines[start:])), sep=";")
    df.columns = [c.strip('"') for c in df.columns]
    df = df[(df["D0"] == "M0") & (df["D1"] == "USD1")].dropna(subset=["Value"])
    df["annee"] = df["Date"].str[:4].astype(int)
    df["mois"] = df["Date"].str[5:7].astype(int)
    return df[["annee", "mois", "Value"]].rename(columns={"Value": "chf_par_usd"})


def main() -> None:
    fx = taux_chf()
    fx_an = fx.groupby("annee")["chf_par_usd"].mean()

    raw = pd.DataFrame(charger("annuel"))
    raw["cmdCode"] = raw["cmdCode"].astype(str)
    raw = raw[raw["cmdCode"].isin(CODES)]
    raw["annee"] = raw["refYear"].astype(int) if "refYear" in raw else raw["period"].astype(str).str[:4].astype(int)
    monde = raw[raw["partnerCode"] == 0]
    det = raw[(raw["partnerCode"] != 0) & raw["partnerISO"].notna()].copy()
    det["partnerISO"] = det["partnerISO"].replace({"S19": "TWN"})   # « Other Asia, nes » = Taïwan dans Comtrade
    det = det[det["partnerISO"].str.fullmatch(r"[A-Z]{3}") & (det["partnerISO"] != "CHE")]

    rows = []
    for r in det.itertuples():
        fr, en, reg = pays(r.partnerISO)
        cat, mat, mvt = CODES[r.cmdCode]
        usd = float(r.primaryValue or 0)
        rows.append({"annee": r.annee, "pays": fr, "pays_en": en, "iso3": r.partnerISO, "region": reg,
                     "code_sh": r.cmdCode, "categorie": cat, "matiere": mat, "mouvement": mvt,
                     "valeur_chf": round(usd * fx_an[r.annee]), "valeur_usd": round(usd),
                     "pieces": int(r.qty) if pd.notna(r.qty) else 0})
    df = pd.DataFrame(rows)
    df = df.groupby(["annee", "pays", "pays_en", "iso3", "region", "code_sh", "categorie", "matiere", "mouvement"],
                    as_index=False)[["valeur_chf", "valeur_usd", "pieces"]].sum()
    tot = df.groupby(["annee", "pays"])["valeur_chf"].sum().rename("tot").reset_index()
    tot["rang_pays"] = tot.groupby("annee")["tot"].rank(ascending=False, method="first").astype(int)
    df = df.merge(tot[["annee", "pays", "rang_pays"]], on=["annee", "pays"])
    df = df.sort_values(["annee", "rang_pays", "code_sh"])
    df.to_csv(OUT / "exportations.csv", index=False)

    # Contrôles : la somme des pays doit retrouver le total « Monde » publié (hors pays non identifiés)
    ctrl = {}
    for y, g in monde.groupby("annee"):
        m = float(g["primaryValue"].sum())
        d = float(det[det["annee"] == y]["primaryValue"].sum())
        ctrl[int(y)] = {"monde_usd": round(m), "somme_pays_usd": round(d), "couverture": round(d / m, 4) if m else None,
                        "pieces_monde": int(g["qty"].sum())}
    (OUT / "controles.json").write_text(json.dumps({
        "annees": ctrl, "lignes_exportations": len(df),
        "pays": int(df["pays"].nunique()), "derniere_annee": int(df["annee"].max())}, ensure_ascii=False, indent=2))
    print(f"{len(df)} lignes annuelles, {df['pays'].nunique()} pays")


if __name__ == "__main__":
    main()
