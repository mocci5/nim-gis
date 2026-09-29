"""NiM-GIS: classe principal del complement."""

from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QMessageBox

try:
    from qgis.PyQt.QtGui import QAction  # QGIS 4 (Qt6)
except ImportError:
    from qgis.PyQt.QtWidgets import QAction  # QGIS 3 (Qt5)

MENU = "&NiM-GIS"


class NimPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.toolbar = None
        self.actions = []

    def initGui(self):  # noqa: N802
        self.toolbar = self.iface.addToolBar("NiM-GIS")
        self.toolbar.setObjectName("NiMGISToolbar")

        accio_info = QAction(
            QgsApplication.getThemeIcon("/mActionHelpContents.svg"),
            "Quant a NiM-GIS",
            self.iface.mainWindow(),
        )
        accio_info.triggered.connect(self.mostra_info)
        self.toolbar.addAction(accio_info)
        self.iface.addPluginToMenu(MENU, accio_info)
        self.actions.append(accio_info)

    def unload(self):
        for accio in self.actions:
            self.iface.removePluginMenu(MENU, accio)
        self.actions = []
        if self.toolbar is not None:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None

    def mostra_info(self):
        QMessageBox.information(
            self.iface.mainWindow(),
            "NiM-GIS",
            "NiM-GIS 0.0.1\n\nComplement en desenvolupament.",
        )
