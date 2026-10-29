"""Contrôles de cohérence que le XSD ne fait pas : références de champs, noms de feuilles, formules."""
import re
import sys
from pathlib import Path

from lxml import etree

TWB = Path(__file__).resolve().parent / "Montres-Suisses.twb"


def main() -> int:
    doc = etree.parse(str(TWB))
    err = []
    sources = {}
    for ds in doc.xpath("/workbook/datasources/datasource"):
        names = {c.get("name") for c in ds.xpath("column")}
        names |= {f"[{c.get('name')}]" for c in ds.xpath(".//relation/columns/column")}
        sources[ds.get("name")] = names
        for c in ds.xpath("column[calculation]"):
            f = c.find("calculation").get("formula")
            for ref in re.findall(r"(?<!\])\[([^\[\]]+)\]", re.sub(r"\[Parameters\]\.\[[^\]]+\]", "", f)):
                if f"[{ref}]" not in names:
                    err.append(f"{c.get('caption')} : champ inconnu [{ref}]")
            if f.count("(") != f.count(")"):
                err.append(f"{c.get('caption')} : parenthèses déséquilibrées")
    sheets = {w.get("name") for w in doc.xpath("/workbook/worksheets/worksheet")}
    for w in doc.xpath("/workbook/worksheets/worksheet"):
        insts = {}
        for dd in w.xpath(".//view/datasource-dependencies"):
            ds = dd.get("datasource")
            cols = {c.get("name") for c in dd.xpath("column")}
            for ci in dd.xpath("column-instance"):
                if ci.get("column") not in cols:
                    err.append(f"{w.get('name')} : instance sans colonne {ci.get('column')}")
                insts[f"[{ds}].{ci.get('name')}"] = 1
            for c in cols:
                if c not in sources.get(ds, set()) and "(generated)" not in c:
                    err.append(f"{w.get('name')} : colonne absente de la source {c}")
        refs = re.findall(r"\[[^\]]+\]\.\[[^\]]+\]", " ".join(w.xpath(".//rows/text()|.//cols/text()")))
        refs += [e.get("column") for e in w.xpath(".//encodings/*")]
        refs += [e.get("column") for e in w.xpath(".//filter|.//computed-sort")]
        refs += [e.get("using") for e in w.xpath(".//computed-sort")]
        for r in refs:
            if r and "(generated)" not in r and r not in insts:
                err.append(f"{w.get('name')} : référence non déclarée {r}")
    for z in doc.xpath("//dashboard//zone[@name]"):
        if z.get("name") not in sheets:
            err.append(f"tableau de bord : feuille inconnue {z.get('name')}")
    for e in err:
        print("ERREUR", e)
    print(f"{len(sheets)} feuilles, {len(doc.xpath('//dashboard'))} tableaux de bord, {len(err)} erreur(s) de cohérence")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
