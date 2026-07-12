"""Caso de uso: descargar por rango de meses e ingerir cada archivo (RF01)."""
from __future__ import annotations

import logging

from ..dominio.modelos import Periodo
from ..dominio.puertos import FuenteArchivosPort, RepositorioTasasPort
from .ingestar_archivo import IngestarArchivoUseCase

log = logging.getLogger(__name__)


class DescargarPeriodoUseCase:
    def __init__(
        self,
        descargador: FuenteArchivosPort,
        ingestar: IngestarArchivoUseCase,
        repositorio: RepositorioTasasPort,
    ) -> None:
        self._descargador = descargador
        self._ingestar = ingestar
        self._repositorio = repositorio

    def ejecutar(self, desde: Periodo, hasta: Periodo, forzar: bool = False) -> list[dict]:
        """Un resumen por período del rango. `forzar` re-descarga aunque el archivo ya
        esté ingerido (útil para el trimestre en curso, que gana hojas cada jornada)."""
        resultados = []
        for periodo in Periodo.rango(desde, hasta):
            nombre = periodo.nombre_archivo
            if not forzar and self._repositorio.nombre_archivo_ingerido(nombre):
                log.info("descarga omitida periodo=%s archivo=%s motivo=ya_ingerido", periodo, nombre)
                resultados.append(
                    {"periodo": str(periodo), "archivo": nombre, "estado": "omitido_ya_ingerido"}
                )
                continue
            archivos = list(self._descargador.obtener(periodo))
            if not archivos:
                log.info("periodo no publicado periodo=%s archivo=%s", periodo, nombre)
                resultados.append(
                    {"periodo": str(periodo), "archivo": nombre, "estado": "no_publicado"}
                )
                continue
            for archivo in archivos:
                resumen = self._ingestar.ejecutar(archivo)
                resultados.append({"periodo": str(periodo), **resumen.como_dict()})
        return resultados
