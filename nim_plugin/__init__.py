"""NiM-GIS: punt d'entrada del complement per a QGIS."""


def classFactory(iface):  # noqa: N802
    from .plugin import NimPlugin

    return NimPlugin(iface)
