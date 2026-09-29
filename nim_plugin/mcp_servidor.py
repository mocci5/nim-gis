"""NiM-GIS: servidor local dins QGIS que rep ordres del servidor MCP."""

import json

from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtNetwork import QHostAddress, QTcpServer

from .mcp_ordres import ORDRES

PORT = 9877


class ServidorMCP(QObject):
    def __init__(self, iface, port=PORT):
        super().__init__()
        self.iface = iface
        self.port = port
        self.servidor = QTcpServer(self)
        self.servidor.newConnection.connect(self._nova_connexio)
        self.buffers = {}

    def inicia(self):
        return self.servidor.listen(QHostAddress("127.0.0.1"), self.port)

    def atura(self):
        for socket in list(self.buffers):
            socket.close()
        self.buffers = {}
        self.servidor.close()

    def _nova_connexio(self):
        while self.servidor.hasPendingConnections():
            socket = self.servidor.nextPendingConnection()
            self.buffers[socket] = b""
            socket.readyRead.connect(lambda s=socket: self._llegeix(s))
            socket.disconnected.connect(lambda s=socket: self._desconnectat(s))

    def _desconnectat(self, socket):
        self.buffers.pop(socket, None)
        socket.deleteLater()

    def _llegeix(self, socket):
        if socket not in self.buffers:
            return
        self.buffers[socket] += bytes(socket.readAll())
        while b"\n" in self.buffers[socket]:
            linia, self.buffers[socket] = self.buffers[socket].split(b"\n", 1)
            if not linia.strip():
                continue
            resposta = self._processa(linia)
            socket.write(json.dumps(resposta, ensure_ascii=False).encode("utf-8") + b"\n")

    def _processa(self, linia):
        try:
            missatge = json.loads(linia.decode("utf-8"))
            nom = missatge.get("ordre")
            params = missatge.get("params") or {}
            funcio = ORDRES.get(nom)
            if funcio is None:
                return {"ok": False, "error": f"Ordre desconeguda: {nom}"}
            return {"ok": True, "resultat": funcio(self.iface, **params)}
        except Exception as error:  # noqa: BLE001
            return {"ok": False, "error": str(error)}
