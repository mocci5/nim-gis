# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2,<3"]
# ///
"""NiM-GIS: servidor MCP que connecta Claude amb el complement de QGIS."""

import json
import socket

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

HOST = "127.0.0.1"
PORT = 9877

mcp = MCPServer("NiM-GIS")


def envia(ordre, **params):
    missatge = json.dumps({"ordre": ordre, "params": params}) + "\n"
    try:
        with socket.create_connection((HOST, PORT), timeout=300) as connexio:
            connexio.sendall(missatge.encode("utf-8"))
            dades = b""
            while not dades.endswith(b"\n"):
                tros = connexio.recv(65536)
                if not tros:
                    break
                dades += tros
    except OSError as error:
        raise ToolError(
            "No es pot connectar amb QGIS. Obre QGIS i activa el servidor MCP de NiM-GIS."
        ) from error
    resposta = json.loads(dades.decode("utf-8"))
    if not resposta.get("ok"):
        raise ToolError(resposta.get("error", "Error desconegut"))
    return resposta["resultat"]


@mcp.tool()
def ping() -> dict:
    """Comprova la connexió amb QGIS i el complement NiM-GIS."""
    return envia("ping")


@mcp.tool()
def info_projecte() -> dict:
    """Informació del projecte obert a QGIS: títol, fitxer, CRS i nombre de capes."""
    return envia("info_projecte")


@mcp.tool()
def llista_capes() -> list:
    """Llista les capes del projecte amb el tipus, el CRS i el nombre d'entitats."""
    return envia("llista_capes")


@mcp.tool()
def cataleg_capes() -> dict:
    """Llista, per categories, les capes oficials disponibles a NiM-GIS
    (ICGC, Cadastre, SIGPAC, medi natural)."""
    return envia("cataleg_capes")


@mcp.tool()
def afegeix_capa_oficial(nom: str) -> dict:
    """Afegeix al projecte una capa oficial del catàleg de NiM-GIS.

    Feu servir el nom exacte que retorna cataleg_capes.
    """
    return envia("afegeix_capa_oficial", nom=nom)


@mcp.tool()
def tipus_projecte() -> dict:
    """Tipus de projecte NiM-GIS disponibles, amb els grups de capes i les capes
    oficials que es carreguen per defecte en cadascun."""
    return envia("tipus_projecte")


@mcp.tool()
def crea_projecte(
    nom: str,
    carpeta: str,
    tipus: str = "General",
    crs: str = "EPSG:25831",
    capes: list[str] | None = None,
) -> dict:
    """Crea un projecte NiM-GIS nou i el desa.

    Crea l'estructura de carpetes (00_Projecte, 01_Dades_origen, 02_Treball,
    03_Resultats, 04_Planols, 05_Documents) dins `carpeta`, els grups de capes
    segons el tipus i les capes oficials indicades (o les per defecte del tipus).
    Si QGIS té canvis sense desar, l'usuari haurà de confirmar-ho a QGIS.
    """
    return envia("crea_projecte", nom=nom, carpeta=carpeta, tipus=tipus, crs=crs, capes=capes)


@mcp.tool()
def organitza_capes() -> dict:
    """Agrupa per tipus (punts, línies, polígons, ràster, serveis web) les capes
    que no són dins de cap grup. No modifica les capes que ja estan agrupades."""
    return envia("organitza_capes")


@mcp.tool()
def desa_projecte() -> dict:
    """Desa el projecte obert a QGIS."""
    return envia("desa_projecte")


if __name__ == "__main__":
    mcp.run()
