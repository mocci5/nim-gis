"""NiM-GIS: ordres que el servidor MCP pot executar dins QGIS.

Només es poden executar les funcions registrades amb @ordre.
"""

from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsWkbTypes

from .capes_oficials import CATALEG, crea_capa

VERSIO = "0.0.1"
ORDRES = {}


def ordre(nom):
    def registra(funcio):
        ORDRES[nom] = funcio
        return funcio

    return registra


@ordre("ping")
def ping(iface):
    return {"pong": True, "versio": VERSIO}


@ordre("info_projecte")
def info_projecte(iface):
    projecte = QgsProject.instance()
    return {
        "titol": projecte.title(),
        "fitxer": projecte.fileName(),
        "crs": projecte.crs().authid(),
        "capes": len(projecte.mapLayers()),
    }


@ordre("llista_capes")
def llista_capes(iface):
    capes = []
    for capa in QgsProject.instance().mapLayers().values():
        info = {"id": capa.id(), "nom": capa.name(), "crs": capa.crs().authid()}
        if isinstance(capa, QgsVectorLayer):
            info["tipus"] = "vectorial"
            info["geometria"] = QgsWkbTypes.displayString(capa.wkbType())
            info["entitats"] = capa.featureCount()
        elif isinstance(capa, QgsRasterLayer):
            info["tipus"] = "ràster"
        else:
            info["tipus"] = "altre"
        capes.append(info)
    return capes


@ordre("cataleg_capes")
def cataleg_capes(iface):
    return {categoria: [e["nom"] for e in capes] for categoria, capes in CATALEG.items()}


@ordre("afegeix_capa_oficial")
def afegeix_capa_oficial(iface, nom):
    for capes in CATALEG.values():
        for entrada in capes:
            if entrada["nom"] == nom:
                capa = crea_capa(entrada)
                if not capa.isValid():
                    raise ValueError(f"No s'ha pogut carregar la capa: {nom}")
                QgsProject.instance().addMapLayer(capa)
                return {"id": capa.id(), "nom": capa.name()}
    raise ValueError(f"No hi ha cap capa al catàleg amb el nom: {nom}")
