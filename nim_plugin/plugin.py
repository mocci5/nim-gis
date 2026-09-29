"""NiM-GIS: classe principal del complement."""

from qgis.core import QgsApplication, QgsProject
from qgis.PyQt.QtWidgets import QMenu, QMessageBox, QToolButton

from .capes_oficials import CATALEG, crea_capa
from .mcp_servidor import PORT, ServidorMCP

try:
    from qgis.PyQt.QtGui import QAction  # QGIS 4 (Qt6)
except ImportError:
    from qgis.PyQt.QtWidgets import QAction  # QGIS 3 (Qt5)

MENU = "&NiM-GIS"
INSTANT_POPUP = getattr(QToolButton, "ToolButtonPopupMode", QToolButton).InstantPopup


class NimPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.toolbar = None
        self.menu_capes = None
        self.accio_mcp = None
        self.servidor = ServidorMCP(iface)
        self.actions = []

    def initGui(self):  # noqa: N802
        self.toolbar = self.iface.addToolBar("NiM-GIS")
        self.toolbar.setObjectName("NiMGISToolbar")
        self._crea_boto_capes()
        self._crea_boto_mcp()
        self._crea_boto_info()

    def _crea_boto_capes(self):
        self.menu_capes = QMenu("Capes oficials", self.iface.mainWindow())
        for categoria, capes in CATALEG.items():
            submenu = self.menu_capes.addMenu(categoria)
            for entrada in capes:
                accio = submenu.addAction(entrada["nom"])
                accio.triggered.connect(lambda _=False, e=entrada: self.afegeix_capa(e))

        boto = QToolButton()
        boto.setIcon(QgsApplication.getThemeIcon("/mActionAddWmsLayer.svg"))
        boto.setToolTip("Capes oficials")
        boto.setMenu(self.menu_capes)
        boto.setPopupMode(INSTANT_POPUP)
        self.toolbar.addWidget(boto)

    def _crea_boto_mcp(self):
        self.accio_mcp = QAction(
            QgsApplication.getThemeIcon("/mIconConnect.svg"),
            "Servidor MCP",
            self.iface.mainWindow(),
        )
        self.accio_mcp.setCheckable(True)
        self.accio_mcp.toggled.connect(self.commuta_mcp)
        self.toolbar.addAction(self.accio_mcp)
        self.iface.addPluginToMenu(MENU, self.accio_mcp)
        self.actions.append(self.accio_mcp)

    def commuta_mcp(self, activa):
        barra = self.iface.messageBar()
        if not activa:
            self.servidor.atura()
            barra.pushInfo("NiM-GIS", "Servidor MCP aturat")
            return
        if self.servidor.inicia():
            barra.pushSuccess("NiM-GIS", f"Servidor MCP actiu al port {PORT}")
        else:
            barra.pushCritical("NiM-GIS", f"No s'ha pogut iniciar el servidor MCP al port {PORT}")
            self.accio_mcp.blockSignals(True)
            self.accio_mcp.setChecked(False)
            self.accio_mcp.blockSignals(False)

    def _crea_boto_info(self):
        accio_info = QAction(
            QgsApplication.getThemeIcon("/mActionHelpContents.svg"),
            "Quant a NiM-GIS",
            self.iface.mainWindow(),
        )
        accio_info.triggered.connect(self.mostra_info)
        self.toolbar.addAction(accio_info)
        self.iface.addPluginToMenu(MENU, accio_info)
        self.actions.append(accio_info)

    def afegeix_capa(self, entrada):
        capa = crea_capa(entrada)
        if capa.isValid():
            QgsProject.instance().addMapLayer(capa)
        else:
            self.iface.messageBar().pushWarning(
                "NiM-GIS", f"No s'ha pogut carregar la capa: {entrada['nom']}"
            )

    def unload(self):
        self.servidor.atura()
        for accio in self.actions:
            self.iface.removePluginMenu(MENU, accio)
        self.actions = []
        if self.menu_capes is not None:
            self.menu_capes.deleteLater()
            self.menu_capes = None
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
