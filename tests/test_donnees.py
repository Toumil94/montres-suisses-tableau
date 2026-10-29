"""Contrôles qualité bloquants : si un test échoue, les nouvelles données ne sont pas publiées."""
import json
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parents[1] / "data" / "donnees"


def exp():
    return pd.read_csv(D / "exportations.csv", dtype={"code_sh": str})


def test_cles_uniques():
    df = exp()
    assert not df.duplicated(["annee", "iso3", "code_sh"]).any()


def test_valeurs_positives():
    df = exp()
    assert (df["valeur_chf"] >= 0).all() and (df["pieces"] >= 0).all()


def test_couverture_des_pays():
    """La somme des pays identifiés doit couvrir au moins 98 % du total « Monde » publié."""
    c = json.loads((D / "controles.json").read_text())
    for annee, v in c["annees"].items():
        if v["couverture"] is not None:
            assert v["couverture"] > 0.98, (annee, v)


def test_ordre_de_grandeur():
    """Les montres-bracelets suisses représentent environ 20 à 30 milliards de CHF par an depuis 2015."""
    df = exp()
    an = df.groupby("annee")["valeur_chf"].sum() / 1e9
    recent = an[an.index >= 2015]
    recent = recent[recent.index < recent.index.max()] if len(recent) > 1 else recent
    assert recent.between(10, 40).all(), an.to_dict()
