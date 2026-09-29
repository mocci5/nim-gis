"""NiM-GIS: diàleg per crear un projecte nou."""

from qgis.core import QgsCoordinateReferenceSystem
from qgis.gui import QgsFileWidget, QgsProjectionSelectionWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from .capes_oficials import CATALEG
from .projecte import CAPES_PER_DEFECTE, TIPUS_PROJECTE


def enum(classe, grup, nom):
    """Accés a enums compatible amb Qt5 i Qt6."""
    return getattr(getattr(classe, grup, classe), nom)


ROL_NOM = enum(Qt, "ItemDataRole", "UserRole")
MARCAT = enum(Qt, "CheckState", "Checked")
DESMARCAT = enum(Qt, "CheckState", "Unchecked")
MARCABLE = enum(Qt, "ItemFlag", "ItemIsUserCheckable")


class DialegProjecte(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NiM-GIS · Nou projecte")
        self.setMinimumWidth(500)

        self.nom = QLineEdit()
        self.nom.setPlaceholderText("p. ex. Xarxa abastament Capellades")

        self.carpeta = QgsFileWidget()
        self.carpeta.setStorageMode(enum(QgsFileWidget, "StorageMode", "GetDirectory"))

        self.tipus = QComboBox()
        self.tipus.addItems(list(TIPUS_PROJECTE))

        self.crs = QgsProjectionSelectionWidget()
        self.crs.setCrs(QgsCoordinateReferenceSystem("EPSG:25831"))

        self.capes = QListWidget()
        for categoria, capes in CATALEG.items():
            for entrada in capes:
                item = QListWidgetItem(f"{categoria} · {entrada['nom']}")
                item.setData(ROL_NOM, entrada["nom"])
                item.setFlags(item.flags() | MARCABLE)
                item.setCheckState(DESMARCAT)
                self.capes.addItem(item)

        self.tipus.currentTextChanged.connect(self._marca_capes_per_defecte)
        self._marca_capes_per_defecte(self.tipus.currentText())

        formulari = QFormLayout()
        formulari.addRow("Nom del projecte", self.nom)
        formulari.addRow("Carpeta on crear-lo", self.carpeta)
        formulari.addRow("Tipus de projecte", self.tipus)
        formulari.addRow("Sistema de coordenades", self.crs)
        formulari.addRow("Capes oficials", self.capes)

        botons = QDialogButtonBox(
            enum(QDialogButtonBox, "StandardButton", "Ok")
            | enum(QDialogButtonBox, "StandardButton", "Cancel")
        )
        botons.accepted.connect(self._accepta)
        botons.rejected.connect(self.reject)

        disseny = QVBoxLayout(self)
        disseny.addLayout(formulari)
        disseny.addWidget(botons)

    def _marca_capes_per_defecte(self, tipus):
        per_defecte = CAPES_PER_DEFECTE.get(tipus, [])
        for i in range(self.capes.count()):
            item = self.capes.item(i)
            item.setCheckState(MARCAT if item.data(ROL_NOM) in per_defecte else DESMARCAT)

    def _accepta(self):
        if not self.nom.text().strip():
            QMessageBox.warning(self, "NiM-GIS", "Cal posar un nom al projecte.")
            return
        if not self.carpeta.filePath():
            QMessageBox.warning(self, "NiM-GIS", "Cal triar una carpeta.")
            return
        self.accept()

    def valors(self):
        capes = []
        for i in range(self.capes.count()):
            item = self.capes.item(i)
            if item.checkState() == MARCAT:
                capes.append(item.data(ROL_NOM))
        return {
            "nom": self.nom.text().strip(),
            "carpeta": self.carpeta.filePath(),
            "tipus": self.tipus.currentText(),
            "crs": self.crs.crs().authid(),
            "capes": capes,
        }
