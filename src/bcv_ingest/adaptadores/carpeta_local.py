"""CarpetaLocalAdapter: fuente de archivos colocados manualmente (RF02, ADR-0002)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from ..dominio.modelos import ArchivoSmc, OrigenArchivo, Periodo
from ..dominio.puertos import FuenteArchivosPort
from .integridad import sha256_de

log = logging.getLogger(__name__)


class CarpetaLocalAdapter(FuenteArchivosPort):
    def __init__(self, ruta: Path) -> None:
        self._ruta = ruta

    def obtener(self, periodo: Periodo | None = None) -> Iterator[ArchivoSmc]:
        if self._ruta.is_file():
            rutas = [self._ruta]
        else:
            rutas = sorted(self._ruta.glob("*.xls"))
        for ruta in rutas:
            archivo = ArchivoSmc(
                ruta=ruta, sha256=sha256_de(ruta), origen=OrigenArchivo.LOCAL
            )
            log.info("archivo local detectado archivo=%s sha256=%s", archivo.nombre, archivo.sha256)
            yield archivo
