"""DescargadorHttpBcv: descarga del portal BCV con TLS estricto (RS01, ADR-0004).

Política de fallo cerrado: la verificación del certificado es obligatoria y este
adaptador NO expone ninguna vía para degradarla (sin flag --inseguro). Ante
certificado inválido la descarga falla con ErrorDescarga; el respaldo operativo es
el modo local (ADR-0002).

La validación usa el almacén de confianza del sistema operativo (truststore) en vez
del bundle certifi: el servidor del BCV envía una cadena incompleta (verificado
2026-07-12 — adjunta un intermedio de otra CA) y solo el verificador del SO puede
resolver el intermedio correcto vía AIA, igual que curl o un navegador. Sigue siendo
verificación estricta: check_hostname y CERT_REQUIRED.

Patrón de URLs confirmado el 2026-07-11 (PRD §Dependencias): un archivo por trimestre,
HTTP 404 limpio para períodos no publicados (histórico desde 2020-TI).
"""
from __future__ import annotations

import logging
import ssl
import time
from pathlib import Path
from typing import Iterator

import httpx
import truststore

from ..dominio.modelos import ArchivoSmc, ErrorDescarga, OrigenArchivo, Periodo
from ..dominio.puertos import FuenteArchivosPort
from .integridad import sha256_de

log = logging.getLogger(__name__)

URL_BASE = "https://www.bcv.org.ve/sites/default/files/EstadisticasGeneral/"


class DescargadorHttpBcv(FuenteArchivosPort):
    def __init__(
        self,
        destino: Path,
        cliente: httpx.Client | None = None,
        reintentos: int = 3,
        pausa_base: float = 1.0,
    ) -> None:
        self._destino = destino
        if cliente is None:
            contexto = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            cliente = httpx.Client(timeout=30.0, verify=contexto)
        self._cliente = cliente
        self._reintentos = reintentos
        self._pausa_base = pausa_base

    def obtener(self, periodo: Periodo | None = None) -> Iterator[ArchivoSmc]:
        if periodo is None:
            raise ValueError("el descargador requiere un período")
        return self._descargar(periodo)

    def _descargar(self, periodo: Periodo) -> Iterator[ArchivoSmc]:
        nombre = periodo.nombre_archivo
        url = URL_BASE + nombre
        respuesta = self._get_con_reintentos(url)
        if respuesta.status_code == 404:
            log.info("periodo no publicado periodo=%s url=%s", periodo, url)
            return
        if respuesta.status_code != 200:
            raise ErrorDescarga(f"HTTP {respuesta.status_code} al descargar {url}")

        self._destino.mkdir(parents=True, exist_ok=True)
        ruta = self._destino / nombre
        temporal = ruta.with_suffix(".xls.parcial")
        temporal.write_bytes(respuesta.content)
        temporal.replace(ruta)
        archivo = ArchivoSmc(ruta=ruta, sha256=sha256_de(ruta), origen=OrigenArchivo.DESCARGA)
        log.info(
            "descarga completada archivo=%s sha256=%s bytes=%d",
            archivo.nombre, archivo.sha256, len(respuesta.content),
        )
        yield archivo

    def _get_con_reintentos(self, url: str) -> httpx.Response:
        ultimo_error: Exception | None = None
        for intento in range(self._reintentos):
            try:
                return self._cliente.get(url)
            except httpx.TransportError as error:
                # incluye fallos TLS: se reintenta por si es transitorio de red, pero
                # jamás se relaja la verificación (ADR-0004)
                ultimo_error = error
                log.warning("intento %d/%d fallido url=%s error=%s",
                            intento + 1, self._reintentos, url, error)
                if intento + 1 < self._reintentos:
                    time.sleep(self._pausa_base * 2**intento)
        raise ErrorDescarga(
            f"fallo de red o TLS tras {self._reintentos} intentos sobre {url}: {ultimo_error}"
        )
