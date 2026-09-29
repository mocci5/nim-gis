"""NiM-GIS: creació i organització de projectes."""

import re
from datetime import date
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsExpressionContextUtils,
    QgsLayerTreeLayer,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)

from .capes_oficials import CATALEG, crea_capa

CARPETES = [
    "00_Projecte",
    "01_Dades_origen/CAD",
    "01_Dades_origen/SHP",
    "01_Dades_origen/Raster",
    "02_Treball",
    "03_Resultats",
    "04_Planols",
    "05_Documents",
]

TIPUS_PROJECTE = {
    "Hidràulica": ["Xarxa existent", "Xarxa projectada", "Afeccions"],
    "Medi ambient": ["Àmbit del projecte", "Medi natural", "Afeccions"],
    "Agronomia": ["Explotació", "Parcel·les", "Medi natural"],
    "Obra civil": ["Traçat", "Serveis afectats", "Expropiacions"],
    "General": ["Dades del projecte"],
}

CAPES_PER_DEFECTE = {
    "Hidràulica": ["Mapa topogràfic ICGC", "Ortofoto ICGC", "Cadastre"],
    "Medi ambient": [
        "Ortofoto ICGC",
        "Xarxa Natura 2000",
        "Espais naturals de protecció especial (ENPE)",
    ],
    "Agronomia": ["Ortofoto ICGC", "SIGPAC - recintes", "Cadastre"],
    "Obra civil": ["Mapa topogràfic ICGC", "Ortofoto ICGC", "Cadastre"],
    "General": ["Mapa topogràfic ICGC"],
}

GRUP_REFERENCIA = "Referència"

ORDRE_GRUPS = ["Punts", "Línies", "Polígons", "Taules", "Ràster", "Serveis web", "Altres"]
PROVEIDORS_WEB = {"wms", "wfs", "wcs", "arcgismapserver", "arcgisfeatureserver"}


def nom_segur(text):
    """Converteix un nom en un nom de fitxer/carpeta vàlid."""
    return re.sub(r"[^\w\-]+", "_", text.strip()).strip("_") or "projecte"


def crea_estructura(carpeta_base, nom):
    arrel = Path(carpeta_base) / nom_segur(nom)
    for subcarpeta in CARPETES:
        (arrel / subcarpeta).mkdir(parents=True, exist_ok=True)
    return arrel


def entrada_cataleg(nom):
    for categoria, capes in CATALEG.items():
        for entrada in capes:
            if entrada["nom"] == nom:
                return categoria, entrada
    raise ValueError(f"No hi ha cap capa al catàleg amb el nom: {nom}")


def crea_projecte(iface, nom, carpeta, tipus="General", crs="EPSG:25831", capes=None):
    if tipus not in TIPUS_PROJECTE:
        raise ValueError(f"Tipus de projecte desconegut: {tipus}")
    if not Path(carpeta).is_dir():
        raise ValueError(f"La carpeta no existeix: {carpeta}")
    if not iface.newProject(True):
        raise RuntimeError("S'ha cancel·lat la creació del projecte.")

    arrel = crea_estructura(carpeta, nom)
    projecte = QgsProject.instance()
    projecte.setTitle(nom)
    projecte.setCrs(QgsCoordinateReferenceSystem(crs))
    projecte.setFilePathStorage(Qgis.FilePathType.Relative)
    QgsExpressionContextUtils.setProjectVariable(projecte, "nim_tipus", tipus)
    QgsExpressionContextUtils.setProjectVariable(
        projecte, "nim_data_creacio", date.today().isoformat()
    )

    arbre = projecte.layerTreeRoot()
    for grup in TIPUS_PROJECTE[tipus]:
        arbre.addGroup(grup)
    referencia = arbre.addGroup(GRUP_REFERENCIA)

    no_carregades = []
    for nom_capa in capes if capes is not None else CAPES_PER_DEFECTE[tipus]:
        try:
            categoria, entrada = entrada_cataleg(nom_capa)
            capa = crea_capa(entrada)
            if not capa.isValid():
                raise ValueError(nom_capa)
        except ValueError:
            no_carregades.append(nom_capa)
            continue
        subgrup = referencia.findGroup(categoria) or referencia.addGroup(categoria)
        projecte.addMapLayer(capa, False)
        subgrup.addLayer(capa)

    fitxer = arrel / "00_Projecte" / f"{nom_segur(nom)}.qgz"
    if not projecte.write(str(fitxer)):
        raise RuntimeError(f"No s'ha pogut desar el projecte a {fitxer}")
    return {"fitxer": str(fitxer), "carpeta": str(arrel), "capes_no_carregades": no_carregades}


def categoria_capa(capa):
    if capa is None:
        return "Altres"
    if capa.providerType() in PROVEIDORS_WEB:
        return "Serveis web"
    if isinstance(capa, QgsRasterLayer):
        return "Ràster"
    if isinstance(capa, QgsVectorLayer):
        tipus = capa.geometryType()
        if tipus == Qgis.GeometryType.Point:
            return "Punts"
        if tipus == Qgis.GeometryType.Line:
            return "Línies"
        if tipus == Qgis.GeometryType.Polygon:
            return "Polígons"
        return "Taules"
    return "Altres"


def organitza_capes():
    """Agrupa per tipus les capes soltes de l'arrel. No toca les capes que ja són en grups."""
    arrel = QgsProject.instance().layerTreeRoot()
    soltes = [node for node in arrel.children() if isinstance(node, QgsLayerTreeLayer)]
    per_grup = {}
    for node in soltes:
        per_grup.setdefault(categoria_capa(node.layer()), []).append(node)

    posicio = 0
    for nom_grup in ORDRE_GRUPS:
        nodes = per_grup.get(nom_grup)
        if not nodes:
            continue
        grup = arrel.findGroup(nom_grup)
        if grup is None:
            grup = arrel.insertGroup(posicio, nom_grup)
        posicio += 1
        for node in sorted(nodes, key=lambda n: n.name().lower()):
            grup.addChildNode(node.clone())
            arrel.removeChildNode(node)

    return {"organitzades": len(soltes), "grups": {g: len(n) for g, n in per_grup.items()}}


def desa_projecte():
    projecte = QgsProject.instance()
    if not projecte.fileName():
        raise ValueError("El projecte encara no s'ha desat mai. Creeu-lo amb NiM-GIS primer.")
    if not projecte.write():
        raise RuntimeError("No s'ha pogut desar el projecte.")
    return {"fitxer": projecte.fileName()}
