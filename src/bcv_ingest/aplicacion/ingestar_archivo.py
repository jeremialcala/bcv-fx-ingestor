"""Caso de uso central: hash -> parseo -> validación -> carga (pipeline único, ADR-0002)."""
from __future__ import annotations

import logging

from ..dominio.modelos import (
    ArchivoIlegibleError,
    ArchivoSmc,
    EstadoIngesta,
    ItemCuarentena,
    ResumenIngesta,
)
from ..dominio.puertos import LectorTasasPort, RepositorioTasasPort
from ..dominio.validador import ValidadorDominio

log = logging.getLogger(__name__)


class IngestarArchivoUseCase:
    def __init__(
        self,
        lector: LectorTasasPort,
        validador: ValidadorDominio,
        repositorio: RepositorioTasasPort,
    ) -> None:
        self._lector = lector
        self._validador = validador
        self._repositorio = repositorio

    def ejecutar(self, archivo: ArchivoSmc) -> ResumenIngesta:
        resumen = ResumenIngesta(
            archivo=archivo.nombre,
            sha256=archivo.sha256,
            origen=archivo.origen.value,
            estado=EstadoIngesta.VALIDANDO.value,
        )
        if self._repositorio.hash_conocido(archivo.sha256):
            resumen.estado = EstadoIngesta.DUPLICADO.value
            log.info("ingesta omitida archivo=%s sha256=%s motivo=hash_conocido",
                     archivo.nombre, archivo.sha256)
            return resumen

        ingesta_id = self._repositorio.registrar_ingesta(archivo, EstadoIngesta.VALIDANDO)
        try:
            self._procesar(archivo, ingesta_id, resumen)
            self._repositorio.actualizar_estado(ingesta_id, EstadoIngesta(resumen.estado))
            self._repositorio.confirmar()
        except Exception:
            # A1: nunca dejar cargas parciales; la transacción del archivo se revierte entera
            self._repositorio.revertir()
            self._repositorio.registrar_ingesta(archivo, EstadoIngesta.FALLIDO)
            self._repositorio.confirmar()
            resumen.estado = EstadoIngesta.FALLIDO.value
            log.exception("ingesta fallida archivo=%s sha256=%s", archivo.nombre, archivo.sha256)
            raise
        log.info(
            "ingesta terminada archivo=%s sha256=%s estado=%s jornadas=%d tasas=%d duplicadas=%d cuarentenas=%d",
            archivo.nombre, archivo.sha256, resumen.estado, resumen.jornadas_cargadas,
            resumen.tasas_cargadas, resumen.duplicadas, len(resumen.cuarentenas),
        )
        return resumen

    def _procesar(self, archivo: ArchivoSmc, ingesta_id: int, resumen: ResumenIngesta) -> None:
        try:
            parseo = self._lector.parsear(archivo)
        except ArchivoIlegibleError as error:
            item = ItemCuarentena(hoja=None, motivo=str(error))
            self._cuarentena(ingesta_id, archivo, item, resumen)
            resumen.estado = EstadoIngesta.CUARENTENA.value
            return

        for item in parseo.descartes:
            self._cuarentena(ingesta_id, archivo, item, resumen)

        for jornada_cruda in parseo.jornadas:
            jornada, items = self._validador.validar(jornada_cruda)
            for item in items:
                self._cuarentena(ingesta_id, archivo, item, resumen)
            if jornada is None:
                continue
            carga = self._repositorio.guardar_jornada(jornada, ingesta_id)
            if carga.jornada_nueva:
                resumen.jornadas_cargadas += 1
            resumen.tasas_cargadas += carga.tasas_nuevas
            resumen.duplicadas += carga.tasas_duplicadas

        hubo_carga = resumen.jornadas_cargadas > 0 or resumen.tasas_cargadas > 0
        if resumen.cuarentenas and hubo_carga:
            resumen.estado = EstadoIngesta.CARGADO_PARCIAL.value
        elif resumen.cuarentenas:
            resumen.estado = EstadoIngesta.CUARENTENA.value
        else:
            resumen.estado = EstadoIngesta.CARGADO.value

    def _cuarentena(
        self,
        ingesta_id: int,
        archivo: ArchivoSmc,
        item: ItemCuarentena,
        resumen: ResumenIngesta,
    ) -> None:
        self._repositorio.enviar_a_cuarentena(ingesta_id, item)
        resumen.cuarentenas.append(item)
        # RS04: cada decisión de cuarentena queda auditada con archivo, hoja y motivo
        log.warning(
            "cuarentena archivo=%s sha256=%s hoja=%s motivo=%r",
            archivo.nombre, archivo.sha256, item.hoja, item.motivo,
        )
