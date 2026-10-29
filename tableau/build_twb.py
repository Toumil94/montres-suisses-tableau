"""Génère le classeur Tableau (TWB, puis TWBX avec les données) à partir de ce script.

« Dashboard as code » : sources, champs calculés, feuilles et tableaux de bord sont décrits
ici, versionnés et validés contre le schéma XSD officiel de Tableau (tableau-document-schemas).

    python tableau/build_twb.py
"""
from __future__ import annotations

import csv
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr, escape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "tableau"
NAME = "Montres-Suisses"
VERSION = "26.1"
NS = uuid.UUID("2b7e1a64-5c0d-4b8e-9f21-7a3c6d9e0f15")

INK, SLATE, GOLD, GREEN, RULE, BG = "#14202B", "#5B6670", "#A37E2C", "#0F5132", "#D9D4C7", "#F7F5EF"


def uid(*p: str) -> str:
    return "{" + str(uuid.uuid5(NS, "/".join(p))).upper() + "}"


def a(v) -> str:
    return quoteattr(str(v))


# =============================================================================
# 1. Sources de données
# =============================================================================
TYPES = {"integer": ("integer", 20, "Sum"), "real": ("real", 5, "Sum"), "string": ("string", 129, "Count"),
         "date": ("date", 133, "Year")}


class Source:
    def __init__(self, key: str, caption: str, csv_name: str, cols: list[tuple[str, str, str, str]]):
        """cols : (nom, type, rôle, libellé)."""
        self.key, self.caption, self.csv = key, caption, csv_name
        self.name = "federated." + uid("ds", key)[1:9].lower() + uid("ds2", key)[1:20].replace("-", "").lower()[:20]
        self.conn = "textscan." + uid("cx", key)[1:20].replace("-", "").lower()
        self.cols = cols
        self.calcs: list[tuple[str, str, str, str, str, str]] = []   # (id, libellé, formule, type, rôle, format)
        self.geo: dict[str, str] = {}

    def calc(self, cid, caption, formula, dtype="real", role="measure", fmt=""):
        self.calcs.append((cid, caption, formula, dtype, role, fmt))
        return cid

    @property
    def table(self):
        return "[" + self.csv.replace(".csv", "#csv") + "]"

    def ref(self, inst: str) -> str:
        return f"[{self.name}].[{inst}]"

    def xml(self) -> str:
        cols = "\n".join(f"            <column datatype={a(TYPES[t][0])} name={a(n)} ordinal='{i}' />"
                         for i, (n, t, _, _) in enumerate(self.cols))
        meta = []
        for i, (n, t, _, _) in enumerate(self.cols):
            dt, rt, agg = TYPES[t]
            meta.append(f"""          <metadata-record class='column'>
            <remote-name>{escape(n)}</remote-name>
            <remote-type>{rt}</remote-type>
            <local-name>[{escape(n)}]</local-name>
            <parent-name>[{escape(self.csv)}]</parent-name>
            <remote-alias>{escape(n)}</remote-alias>
            <ordinal>{i}</ordinal>
            <local-type>{dt}</local-type>
            <aggregation>{agg}</aggregation>
            <contains-null>true</contains-null>
          </metadata-record>""")
        out = [f"""    <datasource caption={a(self.caption)} inline='true' name={a(self.name)} version={a(VERSION)}>
      <connection class='federated'>
        <named-connections>
          <named-connection caption={a(self.caption)} name={a(self.conn)}>
            <connection class='textscan' directory='Data/donnees' filename={a(self.csv)} password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection={a(self.conn)} name={a(self.csv)} table={a(self.table)} type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
{cols}
          </columns>
        </relation>
        <metadata-records>
{chr(10).join(meta)}
        </metadata-records>
      </connection>"""]
        for n, t, role, cap in self.cols:
            dt = TYPES[t][0]
            typ = "quantitative" if role == "measure" else ("ordinal" if dt in ("integer", "date") else "nominal")
            geo = f" semantic-role={a(self.geo[n])}" if n in self.geo else ""
            out.append(f"      <column caption={a(cap)} datatype={a(dt)} name={a('[' + n + ']')} role={a(role)}{geo} type={a(typ)} />")
        for cid, cap, f, dt, role, fmt in self.calcs:
            typ = "quantitative" if role == "measure" else "nominal"
            fm = f" default-format={a(fmt)}" if fmt else ""
            out.append(f"      <column caption={a(cap)} datatype={a(dt)}{fm} name={a('[' + cid + ']')} role={a(role)} type={a(typ)}>\n"
                       f"        <calculation class='tableau' formula={a(f)} />\n      </column>")
        out.append("      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />")
        out.append("    </datasource>")
        return "\n".join(out)


EXP = Source("exp", "Exportations annuelles", "exportations.csv", [
    ("annee", "integer", "dimension", "Année"),
    ("pays", "string", "dimension", "Pays"),
    ("pays_en", "string", "dimension", "Pays (carte)"),
    ("iso3", "string", "dimension", "Code ISO"),
    ("region", "string", "dimension", "Région"),
    ("code_sh", "string", "dimension", "Code SH"),
    ("categorie", "string", "dimension", "Catégorie"),
    ("matiere", "string", "dimension", "Matière de la boîte"),
    ("mouvement", "string", "dimension", "Mouvement"),
    ("valeur_chf", "real", "measure", "Valeur (CHF)"),
    ("valeur_usd", "real", "measure", "Valeur (USD)"),
    ("pieces", "integer", "measure", "Pièces"),
    ("rang_pays", "integer", "measure", "Rang du pays dans l'année"),
])
EXP.geo["pays_en"] = "[Country].[Name]"

MEN = Source("men", "Exportations mensuelles", "mensuel.csv", [
    ("date", "date", "dimension", "Mois"),
    ("code_sh", "string", "dimension", "Code SH"),
    ("matiere", "string", "dimension", "Matière de la boîte"),
    ("mouvement", "string", "dimension", "Mouvement"),
    ("valeur_chf", "real", "measure", "Valeur (CHF)"),
    ("pieces", "integer", "measure", "Pièces"),
])

PARAM = "[Parameters].[Parameter 1]"
P = PARAM   # dans une formule, un paramètre s'écrit [Parameters].[Parameter 1]
MRD = "n#,##0"
FMT_CHF = "n#,##0"
FMT_PCT = "p0.0%"
FMT_EVOL = "p0.0%"

V_AN = EXP.calc("Calc_ValeurAnnee", "Exportations (année)", f"SUM(IF [annee] = {P} THEN [valeur_chf] END)", fmt=MRD)
V_MRD = EXP.calc("Calc_ValeurMrd", "Exportations (Mrd CHF)", "[Calc_ValeurAnnee] / 1000000000", fmt="n#,##0.00")
V_N1 = EXP.calc("Calc_ValeurN1", "Exportations (année précédente)", f"SUM(IF [annee] = {P} - 1 THEN [valeur_chf] END)", fmt=MRD)
EVOL = EXP.calc("Calc_Evolution", "Évolution vs N-1", "([Calc_ValeurAnnee] - [Calc_ValeurN1]) / [Calc_ValeurN1]", fmt=FMT_EVOL)
V_19 = EXP.calc("Calc_Valeur2019", "Exportations 2019", "SUM(IF [annee] = 2019 THEN [valeur_chf] END)", fmt=MRD)
NIV19 = EXP.calc("Calc_Niveau2019", "Niveau vs 2019", "[Calc_ValeurAnnee] / [Calc_Valeur2019]", fmt="p0%")
PCS = EXP.calc("Calc_PiecesAnnee", "Pièces (année)", f"SUM(IF [annee] = {P} THEN [pieces] END)", fmt="n#,##0")
PCS_N1 = EXP.calc("Calc_PiecesN1", "Pièces (année précédente)", f"SUM(IF [annee] = {P} - 1 THEN [pieces] END)", fmt="n#,##0")
PRIX = EXP.calc("Calc_PrixMoyen", "Prix moyen à l'export (CHF par pièce)", "[Calc_ValeurAnnee] / [Calc_PiecesAnnee]", fmt=FMT_CHF)
PRIX_N1 = EXP.calc("Calc_PrixMoyenN1", "Prix moyen N-1", "[Calc_ValeurN1] / [Calc_PiecesN1]", fmt=FMT_CHF)
PRIX_EV = EXP.calc("Calc_PrixEvolution", "Évolution du prix moyen", "([Calc_PrixMoyen] - [Calc_PrixMoyenN1]) / [Calc_PrixMoyenN1]", fmt=FMT_EVOL)
PRIX_ALL = EXP.calc("Calc_PrixMoyenTous", "Prix moyen (CHF par pièce)", "SUM([valeur_chf]) / SUM([pieces])", fmt=FMT_CHF)
MECA = EXP.calc("Calc_PartMeca", "Part des montres mécaniques (valeur)",
                f"SUM(IF [annee] = {P} AND STARTSWITH([mouvement], \"Mécanique\") THEN [valeur_chf] END) / [Calc_ValeurAnnee]", fmt=FMT_PCT)
PREC = EXP.calc("Calc_PartPrecieux", "Part des boîtes en métal précieux (valeur)",
                f"SUM(IF [annee] = {P} AND [matiere] = \"Métal précieux\" THEN [valeur_chf] END) / [Calc_ValeurAnnee]", fmt=FMT_PCT)
TOTAL = EXP.calc("Calc_TotalMonde", "Total des exportations (année)", f"{{FIXED : SUM(IF [annee] = {P} THEN [valeur_chf] END)}}", fmt=MRD)
PDM = EXP.calc("Calc_PartMarche", "Part des exportations suisses", "[Calc_ValeurAnnee] / MIN([Calc_TotalMonde])", fmt=FMT_PCT)
TOP15 = EXP.calc("Calc_Top15", "Top 15 des marchés", f"{{FIXED [pays] : MIN(IF [annee] = {P} THEN [rang_pays] END)}} <= 15",
                 dtype="boolean", role="dimension")
CROISS = EXP.calc("Calc_Contribution", "Contribution à la croissance (CHF)", "[Calc_ValeurAnnee] - [Calc_ValeurN1]", fmt="n#,##0")
PERIODE = EXP.calc("Calc_Periode", "Période", "IF [annee] = " + P + " THEN \"Année sélectionnée\" ELSE \"Autres années\" END",
                   dtype="string", role="dimension")

TOT_MRD = EXP.calc("Calc_ValeurToutesMrd", "Exportations totales (Mrd CHF)", "SUM([valeur_chf]) / 1000000000", fmt="n#,##0.00")
M_MRD = MEN.calc("Calc_MensuelMrd", "Exportations (Mrd CHF)", "SUM([valeur_chf]) / 1000000000", fmt="n#,##0.00")
M_PRIX = MEN.calc("Calc_PrixMensuel", "Prix moyen (CHF par pièce)", "SUM([valeur_chf]) / SUM([pieces])", fmt=FMT_CHF)


def params_xml() -> str:
    return f"""    <datasource hasconnection='false' inline='true' name='Parameters' version={a(VERSION)}>
      <aliases enabled='yes' />
      <column caption='Année' datatype='integer' name='[Parameter 1]' param-domain-type='range' role='measure' type='quantitative' value='{{YEAR}}'>
        <calculation class='tableau' formula='{{YEAR}}' />
        <range granularity='1' max='{{YEAR}}' min='2012' />
      </column>
    </datasource>"""


# =============================================================================
# 2. Feuilles
# =============================================================================
class Inst:
    """Instance de champ utilisée dans une feuille (ex. somme d'une mesure, année discrète)."""

    def __init__(self, src: Source, col: str, deriv: str = "None", kind: str = "nk"):
        self.src, self.col, self.deriv, self.kind = src, col, deriv, kind
        prefix = {"None": "none", "Sum": "sum", "User": "usr", "Avg": "avg", "Year": "yr", "Month": "mn",
                  "Min": "min"}[deriv]
        self.name = f"{prefix}:{col}:{kind}"

    @property
    def ref(self):
        return self.src.ref(self.name)

    @property
    def typ(self):
        return {"nk": "nominal", "ok": "ordinal", "qk": "quantitative"}[self.kind]


def col_decl(src: Source, col: str) -> str:
    for n, t, role, cap in src.cols:
        if n == col:
            dt = TYPES[t][0]
            typ = "quantitative" if role == "measure" else ("ordinal" if dt in ("integer", "date") else "nominal")
            geo = f" semantic-role={a(src.geo[n])}" if n in src.geo else ""
            return f"<column caption={a(cap)} datatype={a(dt)} name={a('[' + n + ']')} role={a(role)}{geo} type={a(typ)} />"
    for cid, cap, f, dt, role, fmt in src.calcs:
        if cid == col:
            typ = "quantitative" if role == "measure" else "nominal"
            fm = f" default-format={a(fmt)}" if fmt else ""
            return (f"<column caption={a(cap)} datatype={a(dt)}{fm} name={a('[' + cid + ']')} role={a(role)} type={a(typ)}>"
                    f"<calculation class='tableau' formula={a(f)} /></column>")
    raise KeyError(col)


def deps(src: Source, insts: list[Inst]) -> list[str]:
    """Colonnes à déclarer : les champs utilisés, plus ceux dont dépendent les calculs."""
    needed: list[str] = []

    def add(c):
        if c in needed:
            return
        for cid, _, f, *_ in src.calcs:
            if cid == c:
                for n, *_ in src.cols:
                    if f"[{n}]" in f:
                        add(n)
                for other, *_ in src.calcs:
                    if f"[{other}]" in f:
                        add(other)
        needed.append(c)

    for i in insts:
        add(i.col)
    return needed


class Sheet:
    def __init__(self, name: str, src: Source, mark: str, rows=(), cols=(), title: str | None = None):
        self.name, self.src, self.mark = name, src, mark
        self.rows, self.cols = list(rows), list(cols)
        self.enc: list[tuple[str, Inst]] = []
        self.filters: list[str] = []
        self.slices: list[str] = []
        self.sort: tuple[Inst, Inst, str] | None = None
        self.title = title
        self.mark_color: str | None = None
        self.labels = False
        self.uses_param = False
        self.extra_insts: list[Inst] = []
        self.size: float | None = None
        self.style: list[str] = []

    def color(self, i: Inst):
        self.enc.append(("color", i)); return self

    def text(self, i: Inst):
        self.enc.append(("text", i)); return self

    def tooltip(self, i: Inst):
        self.enc.append(("tooltip", i)); return self

    def detail(self, i: Inst):
        self.enc.append(("lod", i)); return self

    def sizeby(self, i: Inst):
        self.enc.append(("size", i)); return self

    def insts(self) -> list[Inst]:
        out = []
        for i in [*self.rows, *self.cols, *(e[1] for e in self.enc), *self.extra_insts]:
            if isinstance(i, Inst) and all(i.name != o.name for o in out):
                out.append(i)
        if self.sort:
            for i in self.sort[:2]:
                if all(i.name != o.name for o in out):
                    out.append(i)
        return out

    def shelf(self, items) -> str:
        refs = [i.ref if isinstance(i, Inst) else i for i in items]
        if not refs:
            return ""
        return refs[0] if len(refs) == 1 else "(" + " / ".join(refs) + ")"

    def xml(self) -> str:
        s = self.src
        insts = self.insts()
        dep_cols = deps(s, insts)
        uses_param = any(P in f for cid, _, f, *_ in s.calcs if cid in dep_cols)
        dep = [col_decl(s, c) for c in dep_cols]
        if any("(generated)]" in str(x) for x in [*self.rows, *self.cols]):
            dep += ["<column datatype='real' name='[Latitude (generated)]' role='measure' type='quantitative' user:auto-column='latitude' />",
                    "<column datatype='real' name='[Longitude (generated)]' role='measure' type='quantitative' user:auto-column='longitude' />"]
        dep += [f"<column-instance column={a('[' + i.col + ']')} derivation={a(i.deriv)} name={a('[' + i.name + ']')} "
                f"pivot='key' type={a(i.typ)} />" for i in insts]
        ds = [f"<datasource caption={a(s.caption)} name={a(s.name)} />"]
        pdep = ""
        if uses_param:
            ds.insert(0, "<datasource name='Parameters' />")
            pdep = (f"<datasource-dependencies datasource='Parameters'><column caption='Année' datatype='integer' name='[Parameter 1]' "
                    f"param-domain-type='range' role='measure' type='quantitative' value='{{YEAR}}'>"
                    f"<calculation class='tableau' formula='{{YEAR}}' /><range granularity='1' max='{{YEAR}}' min='2012' />"
                    f"</column></datasource-dependencies>")
        filt = "".join(self.filters)
        sort = ""
        if self.sort:
            dim, meas, direction = self.sort
            sort = f"<computed-sort column={a(dim.ref)} direction={a(direction)} using={a(meas.ref)} />"
        slices = ("<slices>" + "".join(f"<column>{escape(c)}</column>" for c in self.slices) + "</slices>") if self.slices else ""
        enc = "".join(f"<{k} column={a(i.ref)} />" for k, i in self.enc)
        pane_style = []
        if self.mark_color:
            pane_style.append(f"<format attr='mark-color' value={a(self.mark_color)} />")
        if self.labels:
            pane_style.append("<format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' />")
        if self.size:
            pane_style.append(f"<format attr='size' value='{self.size}' />")
        pstyle = f"<style><style-rule element='mark'>{''.join(pane_style)}</style-rule></style>" if pane_style else ""
        title = ""
        if self.title:
            title = (f"<layout-options><title><formatted-text><run bold='true' fontcolor={a(INK)} fontsize='12'>"
                     f"{escape(self.title)}</run></formatted-text></title></layout-options>")
        style = f"<style>{''.join(self.style)}</style>" if self.style else "<style />"
        return f"""    <worksheet name={a(self.name)}>
      {title}
      <table>
        <view>
          <datasources>{''.join(ds)}</datasources>
          {pdep}
          <datasource-dependencies datasource={a(s.name)}>{''.join(dep)}</datasource-dependencies>
          {filt}
          {sort}
          {slices}
          <aggregation value='true' />
        </view>
        {style}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view><breakdown value='auto' /></view>
            <mark class={a(self.mark)} />
            {('<encodings>' + enc + '</encodings>') if enc else ''}
            {pstyle}
          </pane>
        </panes>
        <rows>{escape(self.shelf(self.rows))}</rows>
        <cols>{escape(self.shelf(self.cols))}</cols>
      </table>
      <simple-id uuid={a(uid('ws', self.name))} />
    </worksheet>"""


def topn_filter(sheet: Sheet, inst: Inst):
    sheet.filters.append(
        f"<filter class='categorical' column={a(inst.ref)}><groupfilter function='member' level={a('[' + inst.name + ']')} "
        f"member='true' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")
    sheet.slices.append(inst.ref)
    sheet.extra_insts.append(inst)


def build_sheets() -> list[Sheet]:
    e = EXP
    yr = Inst(e, "annee", "None", "ok")
    sheets = []

    # Tuiles KPI : un indicateur par feuille, affiché en grand
    for key, cid, title in [("KPI Valeur", V_MRD, "Exportations (Mrd CHF)"), ("KPI Évolution", EVOL, "Évolution vs N-1"),
                            ("KPI Prix", PRIX, "Prix moyen par montre"), ("KPI Mécanique", MECA, "Part mécanique"),
                            ("KPI Pièces", PCS, "Montres exportées")]:
        s = Sheet(key, e, "Text", title=title)
        s.text(Inst(e, cid, "User", "qk"))
        s.style.append(f"<style-rule element='cell'><format attr='font-size' value='24' /><format attr='color' value={a(INK)} />"
                       f"<format attr='font-weight' value='bold' /><format attr='text-align' value='center' /></style-rule>")
        sheets.append(s)

    s = Sheet("Tendance", e, "Bar", rows=[Inst(e, TOT_MRD, "User", "qk")], cols=[yr],
              title="Exportations de montres par année (Mrd CHF)")
    s.color(Inst(e, PERIODE, "None", "nk")).tooltip(Inst(e, "pieces", "Sum", "qk"))
    sheets.append(s)

    s = Sheet("Prix moyen", e, "Line", rows=[Inst(e, PRIX_ALL, "User", "qk")], cols=[yr],
              title="Prix moyen à l'export par montre (CHF)")
    s.mark_color = GOLD
    s.labels = True
    sheets.append(s)

    s = Sheet("Mix matière", e, "Bar", rows=[Inst(e, V_MRD, "User", "qk")], cols=[Inst(e, "matiere", "None", "nk")],
              title="Valeur par matière de la boîte")
    s.color(Inst(e, "mouvement", "None", "nk")).tooltip(Inst(e, PRIX, "User", "qk"))
    sheets.append(s)

    pays = Inst(e, "pays", "None", "nk")
    s = Sheet("Top marchés", e, "Bar", rows=[pays], cols=[Inst(e, V_MRD, "User", "qk")],
              title="Top 15 des marchés (valeur de l'année)")
    s.color(Inst(e, EVOL, "User", "qk")).tooltip(Inst(e, PDM, "User", "qk")).tooltip(Inst(e, PRIX, "User", "qk"))
    s.sort = (pays, Inst(e, V_AN, "User", "qk"), "DESC")
    s.labels = True
    topn_filter(s, Inst(e, TOP15, "None", "nk"))
    sheets.append(s)

    s = Sheet("Carte", e, "Multipolygon", rows=[f"[{e.name}].[Latitude (generated)]"],
              cols=[f"[{e.name}].[Longitude (generated)]"], title="Destinations des montres suisses")
    s.detail(Inst(e, "pays_en", "None", "nk")).color(Inst(e, V_AN, "User", "qk")).tooltip(pays).tooltip(Inst(e, EVOL, "User", "qk"))
    sheets.append(s)

    s = Sheet("Prix par marché", e, "Circle", rows=[Inst(e, PRIX, "User", "qk")], cols=[Inst(e, PCS, "User", "qk")],
              title="Volume et prix moyen par marché")
    s.detail(pays).sizeby(Inst(e, V_AN, "User", "qk")).color(Inst(e, "region", "None", "nk"))
    topn_filter(s, Inst(e, TOP15, "None", "nk"))
    sheets.append(s)

    s = Sheet("Segments", e, "Square", rows=[Inst(e, "matiere", "None", "nk")], cols=[Inst(e, "mouvement", "None", "nk")],
              title="Valeur et prix moyen par segment")
    s.color(Inst(e, V_AN, "User", "qk")).text(Inst(e, PRIX, "User", "qk")).tooltip(Inst(e, EVOL, "User", "qk"))
    sheets.append(s)

    s = Sheet("Régions", e, "Bar", rows=[Inst(e, "region", "None", "nk")], cols=[Inst(e, V_MRD, "User", "qk")],
              title="Valeur par région")
    s.color(Inst(e, EVOL, "User", "qk"))
    s.sort = (Inst(e, "region", "None", "nk"), Inst(e, V_AN, "User", "qk"), "DESC")
    s.labels = True
    sheets.append(s)

    m = MEN
    s = Sheet("Courbe mensuelle", m, "Line", rows=[Inst(m, M_MRD, "User", "qk")], cols=[Inst(m, "date", "Month", "ok")],
              title="Exportations mensuelles (CHF), une ligne par année")
    s.color(Inst(m, "date", "Year", "ok"))
    sheets.append(s)
    return sheets


# =============================================================================
# 3. Tableaux de bord
# =============================================================================
class Dash:
    def __init__(self, name: str, title: str, subtitle: str):
        self.name, self.title, self.subtitle = name, title, subtitle
        self.zones: list[str] = []
        self.sheet_names: list[str] = []
        self.n = 10

    def zid(self):
        self.n += 1
        return self.n

    def sheet(self, sheet, x, y, w, h):
        self.zones.append(f"<zone h='{h}' id='{self.zid()}' name={a(sheet)} w='{w}' x='{x}' y='{y}' />")
        self.sheet_names.append(sheet)

    def text(self, runs, x, y, w, h):
        body = "".join(f"<run bold={a('true' if b else 'false')} fontcolor={a(c)} fontsize='{sz}'>{escape(t)}</run>"
                       + ("<run>Æ&#10;</run>" if nl else "") for t, sz, c, b, nl in runs)
        self.zones.append(f"<zone h='{h}' id='{self.zid()}' type-v2='text' w='{w}' x='{x}' y='{y}'>"
                          f"<formatted-text>{body}</formatted-text></zone>")

    def param(self, x, y, w, h, sheet):
        self.zones.append(f"<zone h='{h}' id='{self.zid()}' mode='slider' name={a(sheet)} param={a(PARAM)} "
                          f"type-v2='paramctrl' w='{w}' x='{x}' y='{y}' />")

    def xml(self) -> str:
        z = "\n          ".join(self.zones)
        return f"""    <dashboard name={a(self.name)}>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <zones>
        <zone h='100000' id='4' type-v2='layout-basic' w='100000' x='0' y='0'>
          {z}
        </zone>
      </zones>
      <simple-id uuid={a(uid('db', self.name))} />
    </dashboard>"""


SOURCE_TXT = ("Source : Office fédéral de la douane et de la sécurité des frontières (OFDF), via UN Comtrade (codes SH 9101 et 9102), "
              "valeurs converties en CHF au cours moyen de la BNS. Analyse : Lyes Toumi, github.com/Toumil94/montres-suisses-tableau")


def build_dashboards(year: int) -> list[Dash]:
    out = []
    d = Dash("Vue d'ensemble", "Exportations horlogères suisses", "")
    d.text([("Montres suisses à l'export", 20, INK, True, True),
            ("Moins de montres, plus de valeur : où en est l'horlogerie suisse ?", 11, SLATE, False, False)], 1200, 1000, 70000, 7000)
    d.param(72000, 1000, 26800, 7000, "KPI Valeur")
    for i, k in enumerate(["KPI Valeur", "KPI Évolution", "KPI Pièces", "KPI Prix", "KPI Mécanique"]):
        d.sheet(k, 1200 + i * 19600, 9500, 18800, 13000)
    d.sheet("Tendance", 1200, 24000, 48400, 38000)
    d.sheet("Prix moyen", 50800, 24000, 48000, 38000)
    d.sheet("Mix matière", 1200, 63500, 48400, 32000)
    d.sheet("Segments", 50800, 63500, 48000, 32000)
    d.text([(SOURCE_TXT, 8, SLATE, False, False)], 1200, 96000, 97600, 3500)
    out.append(d)

    d = Dash("Marchés", "Marchés", "")
    d.text([("Où vont les montres suisses ?", 20, INK, True, True),
            ("Destinations, croissance et positionnement prix par pays", 11, SLATE, False, False)], 1200, 1000, 70000, 7000)
    d.param(72000, 1000, 26800, 7000, "Top marchés")
    d.sheet("Carte", 1200, 9500, 58000, 46000)
    d.sheet("Top marchés", 60400, 9500, 38400, 86000)
    d.sheet("Prix par marché", 1200, 56500, 29000, 39000)
    d.sheet("Régions", 31200, 56500, 28000, 39000)
    d.text([(SOURCE_TXT, 8, SLATE, False, False)], 1200, 96000, 97600, 3500)
    out.append(d)

    d = Dash("Saisonnalité", "Saisonnalité", "")
    d.text([("Le rythme de l'année", 20, INK, True, True),
            ("Exportations mensuelles, toutes destinations confondues", 11, SLATE, False, False)], 1200, 1000, 97600, 7000)
    d.sheet("Courbe mensuelle", 1200, 9500, 97600, 85000)
    d.text([(SOURCE_TXT, 8, SLATE, False, False)], 1200, 96000, 97600, 3500)
    out.append(d)
    return out


# =============================================================================
# 4. Assemblage
# =============================================================================
CARDS = """<cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>
        <edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip>
        <strip size='30'><card type='title' /></strip></edge></cards>"""


def latest_year() -> int:
    with open(DATA / "donnees" / "exportations.csv", encoding="utf-8") as f:
        years = {int(r["annee"]) for r in csv.DictReader(f)}
    return max(years)


def build() -> Path:
    year = latest_year()
    sheets = build_sheets()
    dashes = build_dashboards(year)
    windows = [f"    <window class='dashboard' maximized='true' name={a(d.name)}><viewpoints>"
               + "".join(f"<viewpoint name={a(z)} />" for z in d.sheet_names)
               + f"</viewpoints><active id='-1' /><simple-id uuid={a(uid('wd', d.name))} /></window>" for d in dashes]
    windows += [f"    <window class='worksheet' hidden='true' maximized='true' name={a(s.name)}>{CARDS}"
                f"<simple-id uuid={a(uid('ww', s.name))} /></window>" for s in sheets]
    xml = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version={a(VERSION)} source-build='0.0.0 (0000.0.0.0)' source-platform='win' version={a(VERSION)} xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <ManifestByVersion />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{params_xml()}
{EXP.xml()}
{MEN.xml()}
  </datasources>
  <worksheets>
{chr(10).join(s.xml() for s in sheets)}
  </worksheets>
  <dashboards>
{chr(10).join(d.xml() for d in dashes)}
  </dashboards>
  <windows source-height='30'>
{chr(10).join(windows)}
  </windows>
  <explain-data enabled-for-viewer='true' extreme-values-enabled-for-all='true'>
    <explanation-types />
  </explain-data>
</workbook>
""".replace("{YEAR}", str(year))
    twb = OUT / f"{NAME}.twb"
    twb.write_text(xml, encoding="utf-8")
    twbx = OUT / f"{NAME}.twbx"
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(twb, f"{NAME}.twb")
        for f in ("exportations.csv", "mensuel.csv"):
            z.write(DATA / "donnees" / f, f"Data/donnees/{f}")
    return twb


if __name__ == "__main__":
    print(build())
