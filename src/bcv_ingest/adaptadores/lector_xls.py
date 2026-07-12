"""LectorXlsXlrd: parser del layout SMC con contrato de anclas explícito (ADR-0003).

El archivo es entrada no confiable (RS02): límites de tamaño, hojas y filas; si un
ancla no coincide, la hoja completa va a cuarentena — nunca extracción "a mejor
esfuerzo". xlrd no ejecuta macros ni fórmulas.

Layout verificado contra el modelo real `2_1_2a20_smc.xls` (2026-07-12):
fila 2: título "TIPO DE CAMBIO DE REFERENCIA"; fila 4: "Fecha Operacion: DD/MM/YYYY"
y "Fecha Valor: DD/MM/YYYY"; fila 8 cols 2-6: encabezados Moneda/País y BID/ASK de
las dos bases; monedas desde la fila 10 (código en col 1) hasta la primera fila vacía;
momento de publicación en la fila 0 ("DD/MM/YYYY HH:MM AM/PM").
"""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, datetime

import xlrd

from ..dominio.modelos import ArchivoIlegibleError, ArchivoSmc, ItemCuarentena, JornadaCruda, TasaCruda
from ..dominio.puertos import LectorTasasPort, ResultadoParseo

log = logging.getLogger(__name__)

LIMITE_BYTES = 15 * 2**20
LIMITE_HOJAS = 150
LIMITE_FILAS = 300

_FILA_TITULO = 2
_FILA_FECHAS = 4
_FILA_ENCABEZADOS = 8
_FILA_PRIMERA_MONEDA = 10
_COL_CODIGO = 1
_COL_PAIS = 2
_COLS_VALORES = (3, 4, 5, 6)  # usd_bid, usd_ask, bs_bid, bs_ask

_ENCABEZADOS_ESPERADOS = {
    2: "moneda/pais",
    3: "compra (bid)",
    4: "venta (ask)",
    5: "compra (bid)",
    6: "venta (ask)",
}
_PATRON_HOJA = re.compile(r"^\d{8}$")
_PATRON_CODIGO = re.compile(r"^[A-Z]{3}$")
_PATRON_FECHA_OPERACION = re.compile(r"fecha operacion:\s*(\d{2}/\d{2}/\d{4})")
_PATRON_FECHA_VALOR = re.compile(r"fecha valor:\s*(\d{2}/\d{2}/\d{4})")
_PATRON_PUBLICADO = re.compile(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2} [AP]M")


def _normalizar(texto: str) -> str:
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(sin_acentos.casefold().split())


class LectorXlsXlrd(LectorTasasPort):
    def parsear(self, archivo: ArchivoSmc) -> ResultadoParseo:
        if archivo.ruta.stat().st_size > LIMITE_BYTES:
            raise ArchivoIlegibleError(
                f"excede el límite de {LIMITE_BYTES} bytes (RS02)"
            )
        try:
            libro = xlrd.open_workbook(str(archivo.ruta), on_demand=True)
        except Exception as error:  # xlrd lanza XLRDError, CompDocError, struct.error...
            raise ArchivoIlegibleError(f"XLS ilegible: {error}") from error

        if libro.nsheets == 0:
            raise ArchivoIlegibleError("el libro no contiene hojas")
        if libro.nsheets > LIMITE_HOJAS:
            raise ArchivoIlegibleError(
                f"{libro.nsheets} hojas exceden el límite de {LIMITE_HOJAS} (RS02)"
            )

        jornadas: list[JornadaCruda] = []
        descartes: list[ItemCuarentena] = []
        for nombre in libro.sheet_names():
            try:
                hoja = libro.sheet_by_name(nombre)
                resultado = self._parsear_hoja(hoja, nombre)
                libro.unload_sheet(nombre)
            except Exception as error:
                resultado = ItemCuarentena(hoja=nombre, motivo=f"hoja ilegible: {error}")
            if isinstance(resultado, ItemCuarentena):
                descartes.append(resultado)
            else:
                jornadas.append(resultado)
        return ResultadoParseo(jornadas=tuple(jornadas), descartes=tuple(descartes))

    def _parsear_hoja(self, hoja, nombre: str) -> JornadaCruda | ItemCuarentena:
        if not _PATRON_HOJA.match(nombre):
            return ItemCuarentena(hoja=nombre, motivo="nombre de hoja no es DDMMYYYY")
        if hoja.nrows > LIMITE_FILAS:
            return ItemCuarentena(
                hoja=nombre, motivo=f"{hoja.nrows} filas exceden el límite de {LIMITE_FILAS} (RS02)"
            )

        motivo_ancla = self._verificar_anclas(hoja)
        if motivo_ancla:
            return ItemCuarentena(hoja=nombre, motivo=f"ancla de layout no coincide: {motivo_ancla}")

        fecha_operacion = self._fecha_en_fila(hoja, _PATRON_FECHA_OPERACION)
        fecha_valor = self._fecha_en_fila(hoja, _PATRON_FECHA_VALOR)
        if fecha_operacion is None or fecha_valor is None:
            return ItemCuarentena(
                hoja=nombre, motivo="ancla de layout no coincide: fechas de operación/valor ausentes"
            )
        try:
            fecha_hoja = datetime.strptime(nombre, "%d%m%Y").date()
        except ValueError:
            return ItemCuarentena(hoja=nombre, motivo="nombre de hoja no es una fecha válida")
        if fecha_hoja != fecha_operacion:
            return ItemCuarentena(
                hoja=nombre,
                motivo=(
                    f"nombre de hoja ({fecha_hoja.isoformat()}) no coincide con "
                    f"Fecha Operacion ({fecha_operacion.isoformat()})"
                ),
            )

        tasas = self._extraer_tasas(hoja)
        if not tasas:
            return ItemCuarentena(hoja=nombre, motivo="tabla de monedas vacía")

        return JornadaCruda(
            hoja=nombre,
            fecha_operacion=fecha_operacion,
            fecha_valor=fecha_valor,
            publicado_en=self._publicado_en(hoja, fecha_operacion),
            tasas=tuple(tasas),
        )

    def _verificar_anclas(self, hoja) -> str | None:
        textos_titulo = [
            _normalizar(str(hoja.cell_value(_FILA_TITULO, c)))
            for c in range(hoja.ncols)
        ] if hoja.nrows > _FILA_TITULO else []
        if not any("tipo de cambio de referencia" in t for t in textos_titulo):
            return "falta el título 'TIPO DE CAMBIO DE REFERENCIA' en la fila 2"
        if hoja.nrows <= _FILA_ENCABEZADOS:
            return "hoja demasiado corta para contener los encabezados"
        for col, esperado in _ENCABEZADOS_ESPERADOS.items():
            if col >= hoja.ncols:
                return f"falta la columna {col} de encabezados"
            real = _normalizar(str(hoja.cell_value(_FILA_ENCABEZADOS, col)))
            if real != esperado:
                return f"encabezado [{_FILA_ENCABEZADOS},{col}]={real!r}, se esperaba {esperado!r}"
        return None

    def _fecha_en_fila(self, hoja, patron: re.Pattern) -> date | None:
        if hoja.nrows <= _FILA_FECHAS:
            return None
        for col in range(hoja.ncols):
            texto = _normalizar(str(hoja.cell_value(_FILA_FECHAS, col)))
            m = patron.search(texto)
            if m:
                try:
                    return datetime.strptime(m.group(1), "%d/%m/%Y").date()
                except ValueError:
                    return None
        return None

    def _publicado_en(self, hoja, fecha_operacion: date) -> datetime | None:
        # tolerante: el momento de publicación es informativo (columna nullable)
        for col in range(hoja.ncols):
            texto = str(hoja.cell_value(0, col)).strip()
            m = _PATRON_PUBLICADO.search(texto)
            if m:
                try:
                    return datetime.strptime(m.group(0), "%d/%m/%Y %I:%M %p")
                except ValueError:
                    return None
        log.debug("sin momento de publicación en hoja de %s", fecha_operacion.isoformat())
        return None

    def _extraer_tasas(self, hoja) -> list[TasaCruda]:
        tasas = []
        for fila in range(_FILA_PRIMERA_MONEDA, hoja.nrows):
            codigo = str(hoja.cell_value(fila, _COL_CODIGO)).strip()
            if not _PATRON_CODIGO.match(codigo):
                break  # fin de la tabla: fila vacía o notas al pie
            valores = []
            for col in _COLS_VALORES:
                celda = hoja.cell(fila, col)
                valores.append(
                    float(celda.value) if celda.ctype == xlrd.XL_CELL_NUMBER else None
                )
            tasas.append(
                TasaCruda(
                    codigo_moneda=codigo,
                    pais=str(hoja.cell_value(fila, _COL_PAIS)).strip(),
                    usd_bid=valores[0],
                    usd_ask=valores[1],
                    bs_bid=valores[2],
                    bs_ask=valores[3],
                    fila=fila,
                )
            )
        return tasas
