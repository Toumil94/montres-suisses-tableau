"""Chiffres de référence (analyse/chiffres.json) et graphiques (docs/images/).

Ces chiffres servent de recette : le classeur Tableau doit afficher les mêmes.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "donnees"
IMG = ROOT / "docs" / "images"
OUT = ROOT / "analyse"
LUXE = {"910121", "910221"}

INK, SLATE, GOLD, GREEN, GREY = "#14202B", "#5B6670", "#A37E2C", "#0F5132", "#C9CDD1"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#D9D4C7", "axes.labelcolor": SLATE,
    "xtick.color": SLATE, "ytick.color": SLATE, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#ECE9E1", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.dpi": 150, "savefig.bbox": "tight", "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlelocation": "left", "axes.titlecolor": INK,
})


def pct(x):
    return round(100 * float(x), 1)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    d = pd.read_csv(D / "exportations.csv", dtype={"code_sh": str})
    an = d.groupby("annee")[["valeur_chf", "pieces"]].sum()
    an["prix"] = an["valeur_chf"] / an["pieces"]
    y = int(an.index.max())
    k = {"derniere_annee": y, "premiere_annee": int(an.index.min())}

    k["valeur_mrd"] = round(an.loc[y, "valeur_chf"] / 1e9, 2)
    k["valeur_n1_mrd"] = round(an.loc[y - 1, "valeur_chf"] / 1e9, 2)
    k["evolution_vs_n1"] = pct(an.loc[y, "valeur_chf"] / an.loc[y - 1, "valeur_chf"] - 1)
    k["pieces_millions"] = round(an.loc[y, "pieces"] / 1e6, 2)
    k["prix_moyen_chf"] = round(an.loc[y, "prix"])
    base = int(an.index.min())
    k["depuis"] = base
    k["valeur_vs_debut"] = pct(an.loc[y, "valeur_chf"] / an.loc[base, "valeur_chf"] - 1)
    k["pieces_vs_debut"] = pct(an.loc[y, "pieces"] / an.loc[base, "pieces"] - 1)
    k["prix_vs_debut"] = pct(an.loc[y, "prix"] / an.loc[base, "prix"] - 1)

    cur = d[d["annee"] == y]
    k["part_mecanique"] = pct(cur[cur["mouvement"].str.startswith("Mécanique")]["valeur_chf"].sum() / cur["valeur_chf"].sum())
    k["part_metal_precieux"] = pct(cur[cur["matiere"] == "Métal précieux"]["valeur_chf"].sum() / cur["valeur_chf"].sum())
    lux = cur[cur["code_sh"].isin(LUXE)]
    k["luxe_valeur_mrd"] = round(lux["valeur_chf"].sum() / 1e9, 2)
    k["luxe_part"] = pct(lux["valeur_chf"].sum() / cur["valeur_chf"].sum())
    k["luxe_pieces_millions"] = round(lux["pieces"].sum() / 1e6, 2)
    k["luxe_prix_moyen"] = round(lux["valeur_chf"].sum() / lux["pieces"].sum())
    k["luxe_part_or"] = pct(lux[lux["code_sh"] == "910121"]["valeur_chf"].sum() / lux["valeur_chf"].sum())
    for code, nom in (("910221", "acier"), ("910121", "or")):
        s = d[d["code_sh"] == code].groupby("annee")[["valeur_chf", "pieces"]].sum()
        k[f"prix_auto_{nom}"] = round(s.loc[y, "valeur_chf"] / s.loc[y, "pieces"])
        k[f"prix_auto_{nom}_debut"] = round(s.loc[base, "valeur_chf"] / s.loc[base, "pieces"])

    p = d.groupby(["annee", "pays"])["valeur_chf"].sum().unstack(0)
    top = p[y].sort_values(ascending=False).head(15)
    k["top_marches"] = [{"pays": c, "valeur_mrd": round(v / 1e9, 2), "part": pct(v / cur["valeur_chf"].sum()),
                         "evolution": pct(v / p.loc[c, y - 1] - 1) if p.loc[c, y - 1] else None} for c, v in top.items()]
    reg = cur.groupby("region")["valeur_chf"].sum().sort_values(ascending=False)
    k["regions"] = {r: pct(v / reg.sum()) for r, v in reg.items()}
    k["part_top5"] = pct(top.head(5).sum() / cur["valeur_chf"].sum())

    # 1. Moins de montres, plus de valeur (indice 100 = première année)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for col, c, lab in (("valeur_chf", INK, "Valeur"), ("pieces", GREY, "Pièces"), ("prix", GOLD, "Prix moyen")):
        s = 100 * an[col] / an.loc[base, col]
        ax.plot(an.index, s, color=c, lw=2.4 if col != "pieces" else 2)
        ax.text(y + 0.3, s.iloc[-1], f"{lab} {s.iloc[-1]:.0f}", color=c, va="center", fontsize=9, fontweight="bold")
    ax.axhline(100, color=SLATE, lw=0.8, ls=(0, (3, 3)))
    ax.set_xlim(base, y + 3.2)
    ax.xaxis.set_major_locator(mt.MultipleLocator(2))
    ax.set_title(f"Montres suisses exportées, indice 100 = {base}")
    fig.savefig(IMG / "01_valeur_pieces_prix.png")
    plt.close(fig)

    # 2. Prix moyen d'une automatique, acier et or
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for code, c, lab in (("910121", GOLD, "Or (9101.21)"), ("910221", INK, "Acier (9102.21)")):
        s = d[d["code_sh"] == code].groupby("annee")[["valeur_chf", "pieces"]].sum()
        pr = s["valeur_chf"] / s["pieces"]
        ax.plot(pr.index, pr, color=c, lw=2.4, marker="o", ms=3)
        ax.text(y + 0.3, pr.iloc[-1], f"{lab}\n{pr.iloc[-1]:,.0f} CHF".replace(",", " "), color=c, va="center", fontsize=8.5)
    ax.set_yscale("log")
    ax.yaxis.set_minor_formatter(mt.NullFormatter())
    ax.set_yticks([1000, 2000, 5000, 10000, 20000, 40000])
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", " ")))
    ax.set_xlim(base, y + 3.5)
    ax.set_title("Prix moyen à l'export d'une montre automatique (CHF, échelle log)")
    fig.savefig(IMG / "02_prix_automatiques.png")
    plt.close(fig)

    # 3. Top 15 des marchés
    fig, ax = plt.subplots(figsize=(8, 5))
    t = top.iloc[::-1] / 1e9
    ev = [(p.loc[c, y] / p.loc[c, y - 1] - 1) if p.loc[c, y - 1] else 0 for c in t.index]
    ax.barh(t.index, t.values, color=[GREEN if e >= 0 else "#9B2C2C" for e in ev], height=0.68)
    for i, (v, e) in enumerate(zip(t.values, ev)):
        ax.text(v + 0.03, i, f"{v:.2f}  ({100 * e:+.1f} %)", va="center", fontsize=8, color=SLATE)
    ax.set_xlim(0, t.max() * 1.3)
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Top 15 des marchés en {y} (Mrd CHF, évolution vs {y - 1})")
    fig.savefig(IMG / "03_top_marches.png")
    plt.close(fig)

    (OUT / "chiffres.json").write_text(json.dumps(k, ensure_ascii=False, indent=2))
    print(json.dumps(k, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
