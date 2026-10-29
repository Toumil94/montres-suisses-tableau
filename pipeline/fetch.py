"""Télécharge les données brutes (exécuté par GitHub Actions).

- UN Comtrade (API publique, sans clé) : exportations suisses de montres (SH 9101 et 9102),
  par pays de destination et par code à 6 chiffres. Source primaire : Office fédéral de la
  douane et de la sécurité des frontières (OFDF), transmise à l'ONU.
- Banque nationale suisse (BNS) : cours moyens mensuels des devises, pour convertir USD en CHF.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
API = "https://comtradeapi.un.org/public/v1/preview/C/{freq}/HS"
CODES = ["910111", "910112", "910119", "910121", "910129", "910191", "910199",
         "910211", "910212", "910219", "910221", "910229", "910291", "910299"]
YEARS = range(2012, 2026)
S = requests.Session()
S.headers["User-Agent"] = "montres-suisses-tableau (projet open source, github.com/Toumil94)"


ERREURS: list[str] = []


def get(url: str, params: dict, tries: int = 8):
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r
            msg = f"HTTP {r.status_code} {r.text[:150]}"
            if r.status_code == 429:   # limite de débit de l'API publique : on attend ce qu'elle demande
                m = re.search(r"(\d+) seconds", r.text)
                time.sleep(int(m.group(1)) + 2 if m else 10)
                continue
        except requests.RequestException as e:
            msg = f"erreur réseau : {str(e)[:150]}"
        print("  " + msg, flush=True)
        if len(ERREURS) < 5:
            ERREURS.append(msg)
        time.sleep(3 * (i + 1))
    return None


def comtrade(freq: str, **params) -> list[dict]:
    p = {"reporterCode": 757, "flowCode": "X", "partner2Code": 0, "customsCode": "C00", "motCode": 0,
         "includeDesc": "true", **params}
    r = get(API.format(freq=freq), p)
    time.sleep(2.5)
    if r is None:
        print(f"::warning title=Comtrade::échec {freq} {params}")
        return []
    js = r.json()
    rows = js.get("data") or []
    if js.get("count", len(rows)) >= 500 or len(rows) >= 500:
        print(f"::warning title=Comtrade::limite de 500 lignes atteinte {params}")
    return rows


def main() -> int:
    t0 = time.time()
    probe = get(API.format(freq="A"), {"reporterCode": 757, "flowCode": "X", "period": 2024, "cmdCode": "910221",
                                       "partnerCode": 0, "includeDesc": "true"})
    print(f"::notice title=Sonde Comtrade::{'ok ' + probe.text[:300] if probe is not None else ERREURS}")
    if probe is None:
        return 1
    ref = get("https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json", {})
    if ref is not None:
        (RAW / "partnerAreas.json").write_text(ref.text, encoding="utf-8")

    # Un fichier par année : une collecte interrompue reprend là où elle s'est arrêtée.
    # Les deux dernières années sont toujours re-téléchargées (révisions des douanes).
    dossier = RAW / "annuel"
    dossier.mkdir(exist_ok=True)
    derniere = max(YEARS)
    for y in YEARS:
        f = dossier / f"{y}.json"
        if f.exists() and y < derniere - 1:
            continue
        rows = []
        for c in CODES:
            rows += comtrade("A", period=y, cmdCode=c)
        print(f"{y} : {len(rows)} lignes ({time.time() - t0:.0f} s)", flush=True)
        if rows:
            f.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        else:
            print(f"::warning title=Comtrade::aucune donnée annuelle pour {y}")
    annual = [r for f in sorted(dossier.glob("*.json")) for r in json.loads(f.read_text(encoding="utf-8"))]

    dossier_m = RAW / "mensuel"
    dossier_m.mkdir(exist_ok=True)
    for y in range(2018, 2027):
        f = dossier_m / f"{y}.json"
        if f.exists() and y < 2025:
            continue
        periods = ",".join(f"{y}{m:02d}" for m in range(1, 13))
        rows = []
        for c in (CODES[:7], CODES[7:]):
            rows += comtrade("M", period=periods, partnerCode=0, cmdCode=",".join(c))
        if rows:
            f.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    monthly = [r for f in sorted(dossier_m.glob("*.json")) for r in json.loads(f.read_text(encoding="utf-8"))]

    snb = get("https://data.snb.ch/api/cube/devkum/data/csv/fr", {})
    if snb is not None:
        (RAW / "snb_devkum.csv").write_text(snb.text, encoding="utf-8")

    print(f"::notice title=Erreurs::{ERREURS}")
    print(f"::notice title=Collecte::{time.time() - t0:.0f} s, {len(annual)} lignes annuelles, {len(monthly)} lignes mensuelles, "
          f"BNS {'ok' if snb is not None else 'échec'}")
    return 0 if annual else 1


if __name__ == "__main__":
    sys.exit(main())
