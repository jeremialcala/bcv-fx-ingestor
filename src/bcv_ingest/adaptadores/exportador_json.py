"""ExportadorJsonLocal: materializa la publicación como archivos JSON (ADR-0007).

Escribe bajo `<destino>/publicacion/` en UTF-8 explícito (en Windows, `write_text`
sin encoding usa cp1252 y rompe "Turquía"/"Perú"). Rechaza rutas fuera del prefijo
(defensa en profundidad, espejo de RS08: el mapeo de claves es cerrado).
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from ..dominio.puertos import ExportadorPublicacionPort


class ExportadorJsonLocal(ExportadorPublicacionPort):
    def __init__(self, destino: str | Path) -> None:
        self._raiz = Path(destino) / "publicacion"

    def escribir(self, ruta_relativa: str, datos: dict) -> None:
        relativa = PurePosixPath(ruta_relativa)
        if relativa.is_absolute() or ".." in relativa.parts:
            raise ValueError(f"ruta fuera del prefijo de publicación: {ruta_relativa!r}")
        ruta = self._raiz / relativa
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
