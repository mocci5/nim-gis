"""NiM-GIS: catàleg de capes oficials."""

from qgis.core import QgsDataSourceUri, QgsRasterLayer, QgsVectorLayer

ICGC_WMS = "https://geoserveis.icgc.cat/servei/catalunya/mapa-base/wms"

CATALEG = {
    "Cartografia base (ICGC)": [
        {"nom": "Mapa topogràfic ICGC", "tipus": "wms", "url": ICGC_WMS, "capa": "topografic"},
        {"nom": "Ortofoto ICGC", "tipus": "wms", "url": ICGC_WMS, "capa": "orto"},
    ],
    "Cadastre i agricultura": [
        {
            "nom": "Cadastre",
            "tipus": "wms",
            "url": "http://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx",
            "capa": "Catastro",
        },
        {
            "nom": "SIGPAC - recintes",
            "tipus": "wms",
            "url": "https://wms.mapa.gob.es/sigpac/wms",
            "capa": "recinto",  # per verificar
        },
    ],
    "Medi natural": [
        {
            "nom": "Xarxa Natura 2000",
            "tipus": "arcgis",
            "url": "https://agportal.sig.gencat.cat/server/rest/services/Xarxa_Natura_2000/MapServer/0",
        },
        {
            "nom": "Espais naturals de protecció especial (ENPE)",
            "tipus": "arcgis",
            "url": "https://gissrv.diba.cat/arcgis/rest/services/SITXELL/ENPE/MapServer/0",
        },
    ],
}


def crea_capa(entrada):
    """Crea la capa QGIS a partir d'una entrada del catàleg."""
    if entrada["tipus"] == "wms":
        uri = QgsDataSourceUri()
        uri.setParam("url", entrada["url"])
        uri.setParam("layers", entrada["capa"])
        uri.setParam("styles", "")
        uri.setParam("format", "image/png")
        uri.setParam("crs", "EPSG:25831")
        return QgsRasterLayer(bytes(uri.encodedUri()).decode(), entrada["nom"], "wms")

    if entrada["tipus"] == "arcgis":
        uri = f"crs='EPSG:25831' url='{entrada['url']}'"
        return QgsVectorLayer(uri, entrada["nom"], "arcgisfeatureserver")

    raise ValueError(f"Tipus de capa desconegut: {entrada['tipus']}")
