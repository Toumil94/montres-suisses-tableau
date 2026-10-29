"""Valide le classeur contre le schéma XSD officiel de Tableau (github.com/tableau/tableau-document-schemas).

    python tableau/validate_twb.py [chemin_local_du_xsd]

Le schéma importe deux espaces de noms sans fournir leur définition (xml et user) :
on fournit ici des définitions minimales, permissives, pour pouvoir valider le reste.
"""
import sys
import tempfile
import urllib.request
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
XSD_URL = "https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/2026_1/twb_2026.1.0.xsd"
XS = "http://www.w3.org/2001/XMLSchema"

USER_XSD = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://www.tableausoftware.com/xml/user">
  <xs:attributeGroup name="UserAttributes-AG"><xs:anyAttribute namespace="##targetNamespace" processContents="skip"/></xs:attributeGroup>
</xs:schema>"""
XML_XSD = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="http://www.w3.org/XML/1998/namespace">
  <xs:attribute name="base" type="xs:anyURI"/>
</xs:schema>"""


def load_schema(raw: bytes) -> etree.XMLSchema:
    tmp = Path(tempfile.mkdtemp())
    (tmp / "user.xsd").write_text(USER_XSD)
    (tmp / "xml.xsd").write_text(XML_XSD)
    root = etree.fromstring(raw)
    for imp in root.findall(f"{{{XS}}}import"):
        ns = imp.get("namespace")
        imp.set("schemaLocation", str(tmp / ("user.xsd" if ns.endswith("/user") else "xml.xsd")))
    return etree.XMLSchema(root)


def main() -> int:
    local = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    raw = local.read_bytes() if local else urllib.request.urlopen(XSD_URL, timeout=60).read()
    schema = load_schema(raw)
    doc = etree.parse(str(HERE / "Montres-Suisses.twb"))
    ok = schema.validate(doc)
    for e in schema.error_log:
        print(f"ligne {e.line} : {e.message}")
    print("Classeur conforme au schéma Tableau 2026.1" if ok else f"{len(schema.error_log)} erreur(s)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
