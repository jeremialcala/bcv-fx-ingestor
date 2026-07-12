"""Hash de integridad de archivos (RS04)."""
import hashlib
from pathlib import Path


def sha256_de(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with open(ruta, "rb") as archivo:
        while bloque := archivo.read(65536):
            resumen.update(bloque)
    return resumen.hexdigest()
