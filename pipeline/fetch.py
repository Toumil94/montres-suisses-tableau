"""Télécharge les données brutes (exécuté par GitHub Actions).

- UN Comtrade (API publique, sans clé) : exportations suisses de montres (SH 9101 et 9102),
  par pays de destination et par code à 6 chiffres. Source primaire : Office fédéral de la
  douane et de la sécurité des frontières (OFDF), transmise à l'ONU.
- Banque nationale suisse (BNS) : cours moyens mensuels des devises, pour convertir USD en CHF.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
API = "https://comtradeapi.un.org/public/v1/preview/C/{freq}/HS"
CODES = ["910111", "910112", "910119", "910121", "910129", "910191", "910199",
         "910211", "910212", "910219", "910221", "910229", "910291", "910299"]
YEARS = range(2010, 2026)
S = requests.Session()
S.headers["User-Agent"] = "montres-suisses-tableau (projet open source, github.com/Toumil94)"


def get(url: str, params: dict, tries: int = 6):
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r
            print(f"  HTTP {r.status_code} {r.text[:200]}")
        except requests.RequestException as e:
            print(f"  erreur réseau : {e}")
        time.sleep(5 * (i + 1))
    return None


def comtrade(freq: str, **params) -> list[dict]:
    p = {"reporterCode": 757, "flowCode": "X", "partner2Code": 0, "customsCode": "C00", "motCode": 0,
         "includeDesc": "true", **params}
    r = get(API.format(freq=freq), p)
    time.sleep(1.2)
    if r is None:
        print(f"::warning title=Comtrade::échec {freq} {params}")
        return []
    js = r.json()
    rows = js.get("data") or []
    if js.get("count", len(rows)) >= 500 or len(rows) >= 500:
        print(f"::warning title=Comtrade::limite de 500 lignes atteinte {params}")
    return rows


def main() -> int:
    ref = get("https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json", {})
    if ref is not None:
        (RAW / "partnerAreas.json").write_text(ref.text, encoding="utf-8")

    annual = []
    for y in YEARS:
        n = 0
        for c in CODES:
            rows = comtrade("A", period=y, cmdCode=c)
            annual += rows
            n += len(rows)
        print(f"{y} : {n} lignes")
        if n == 0:
            print(f"::warning title=Comtrade::aucune donnée annuelle pour {y}")
    (RAW / "comtrade_annuel.json").write_text(json.dumps(annual, ensure_ascii=False), encoding="utf-8")

    monthly = []
    for y in range(2018, 2027):
        periods = ",".join(f"{y}{m:02d}" for m in range(1, 13))
        for c in (CODES[:7], CODES[7:]):
            monthly += comtrade("M", period=periods, partnerCode=0, cmdCode=",".join(c))
    (RAW / "comtrade_mensuel.json").write_text(json.dumps(monthly, ensure_ascii=False), encoding="utf-8")

    snb = get("https://data.snb.ch/api/cube/devkum/data/csv/fr", {})
    if snb is not None:
        (RAW / "snb_devkum.csv").write_text(snb.text, encoding="utf-8")

    print(f"::notice title=Collecte::{len(annual)} lignes annuelles, {len(monthly)} lignes mensuelles, "
          f"BNS {'ok' if snb is not None else 'échec'}")
    return 0 if annual else 1


if __name__ == "__main__":
    sys.exit(main())
