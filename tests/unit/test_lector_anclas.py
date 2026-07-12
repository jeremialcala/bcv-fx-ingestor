"""Negativos del contrato de anclas (ADR-0003, amenaza T1 — la mejor puntuada del DREAD).

El fixture real solo ejercita el camino feliz del parser; aquí cada ancla se rompe
una a una con hojas falsas duck-typed (el lector solo usa nrows/ncols/cell_value/cell),
a través de la API pública `parsear` con el workbook simulado.
"""
from datetime import date
from types import SimpleNamespace

import pytest
import xlrd

from bcv_ingest.adaptadores import lector_xls
from bcv_ingest.adaptadores.lector_xls import LectorXlsXlrd
from bcv_ingest.dominio.modelos import ArchivoIlegibleError, ArchivoSmc, OrigenArchivo


class HojaFalsa:
    def __init__(self, celdas, nrows=12, ncols=7):
        self._celdas = dict(celdas)
        self.nrows = nrows
        self.ncols = ncols

    def cell_value(self, fila, col):
        return self._celdas.get((fila, col), "")

    def cell(self, fila, col):
        valor = self._celdas.get((fila, col), "")
        if isinstance(valor, float):
            ctype = xlrd.XL_CELL_NUMBER
        elif valor:
            ctype = xlrd.XL_CELL_TEXT
        else:
            ctype = xlrd.XL_CELL_EMPTY
        return SimpleNamespace(value=valor, ctype=ctype)


class LibroFalso:
    def __init__(self, hojas):
        self._hojas = dict(hojas)
        self.nsheets = len(self._hojas)

    def sheet_names(self):
        return list(self._hojas)

    def sheet_by_name(self, nombre):
        hoja = self._hojas[nombre]
        if isinstance(hoja, Exception):
            raise hoja
        return hoja

    def unload_sheet(self, nombre):
        pass


def celdas_validas():
    return {
        (0, 6): "31/03/2020 03:49 PM",
        (2, 4): "TIPO DE CAMBIO DE REFERENCIA (*)",
        (4, 1): "Fecha Operacion: 31/03/2020",
        (4, 3): "Fecha Valor: 01/04/2020",
        (8, 2): "Moneda/País",
        (8, 3): "Compra (BID)",
        (8, 4): "Venta (ASK)",
        (8, 5): "Compra (BID)",
        (8, 6): "Venta (ASK)",
        (10, 1): "USD",
        (10, 2): "E.U.A.",
        (10, 3): 1.0,
        (10, 4): 1.0,
        (10, 5): 80743.36,
        (10, 6): 80945.72,
    }


def parsear(monkeypatch, tmp_path, hojas):
    ruta = tmp_path / "falso.xls"
    ruta.write_bytes(b"contenido irrelevante: el workbook esta simulado")
    monkeypatch.setattr(
        lector_xls.xlrd, "open_workbook", lambda *a, **k: LibroFalso(hojas)
    )
    archivo = ArchivoSmc(ruta=ruta, sha256="0" * 64, origen=OrigenArchivo.LOCAL)
    return LectorXlsXlrd().parsear(archivo)


def unico_descarte(resultado):
    assert resultado.jornadas == ()
    assert len(resultado.descartes) == 1
    return resultado.descartes[0]


def test_hoja_falsa_de_referencia_es_valida(monkeypatch, tmp_path):
    # sanidad: la hoja base parsea; cada test siguiente rompe UNA sola ancla
    resultado = parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas_validas())})
    assert resultado.descartes == ()
    jornada = resultado.jornadas[0]
    assert jornada.fecha_operacion == date(2020, 3, 31)
    assert jornada.tasas[0].codigo_moneda == "USD"


def test_nombre_de_hoja_no_es_ddmmyyyy(monkeypatch, tmp_path):
    descarte = unico_descarte(
        parsear(monkeypatch, tmp_path, {"Resumen": HojaFalsa(celdas_validas())})
    )
    assert "DDMMYYYY" in descarte.motivo


def test_nombre_de_hoja_no_es_fecha_valida(monkeypatch, tmp_path):
    celdas = celdas_validas()
    descarte = unico_descarte(parsear(monkeypatch, tmp_path, {"99999999": HojaFalsa(celdas)}))
    assert "fecha válida" in descarte.motivo


def test_falta_el_titulo(monkeypatch, tmp_path):
    celdas = celdas_validas()
    del celdas[(2, 4)]
    descarte = unico_descarte(parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)}))
    assert "ancla" in descarte.motivo and "título" in descarte.motivo


def test_hoja_demasiado_corta(monkeypatch, tmp_path):
    descarte = unico_descarte(
        parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas_validas(), nrows=5)})
    )
    assert "corta" in descarte.motivo


def test_faltan_columnas_de_encabezados(monkeypatch, tmp_path):
    descarte = unico_descarte(
        parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas_validas(), ncols=5)})
    )
    assert "falta la columna" in descarte.motivo


def test_encabezado_no_coincide(monkeypatch, tmp_path):
    celdas = celdas_validas()
    celdas[(8, 3)] = "Compra"  # sin "(BID)"
    descarte = unico_descarte(parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)}))
    assert "encabezado" in descarte.motivo


def test_fecha_de_operacion_ausente(monkeypatch, tmp_path):
    celdas = celdas_validas()
    del celdas[(4, 1)]
    descarte = unico_descarte(parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)}))
    assert "ausentes" in descarte.motivo


def test_fecha_de_operacion_malformada(monkeypatch, tmp_path):
    celdas = celdas_validas()
    celdas[(4, 1)] = "Fecha Operacion: 99/99/2020"
    descarte = unico_descarte(parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)}))
    assert "ausentes" in descarte.motivo


def test_nombre_de_hoja_distinto_de_fecha_operacion(monkeypatch, tmp_path):
    descarte = unico_descarte(
        parsear(monkeypatch, tmp_path, {"30032020": HojaFalsa(celdas_validas())})
    )
    assert "no coincide" in descarte.motivo


def test_tabla_de_monedas_vacia(monkeypatch, tmp_path):
    celdas = {k: v for k, v in celdas_validas().items() if k[0] != 10}
    descarte = unico_descarte(parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)}))
    assert "vacía" in descarte.motivo


def test_publicado_ausente_es_tolerado(monkeypatch, tmp_path):
    celdas = celdas_validas()
    del celdas[(0, 6)]
    resultado = parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)})
    assert resultado.jornadas[0].publicado_en is None  # columna nullable, no cuarentena


def test_publicado_malformado_es_tolerado(monkeypatch, tmp_path):
    celdas = celdas_validas()
    celdas[(0, 6)] = "99/99/2020 03:49 PM"
    resultado = parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)})
    assert resultado.jornadas[0].publicado_en is None


def test_celda_de_valor_no_numerica_llega_como_ausente(monkeypatch, tmp_path):
    celdas = celdas_validas()
    celdas[(10, 3)] = "n/d"
    resultado = parsear(monkeypatch, tmp_path, {"31032020": HojaFalsa(celdas)})
    assert resultado.jornadas[0].tasas[0].usd_bid is None  # la juzga el Validador


def test_libro_sin_hojas_es_ilegible(monkeypatch, tmp_path):
    with pytest.raises(ArchivoIlegibleError, match="no contiene hojas"):
        parsear(monkeypatch, tmp_path, {})


def test_hoja_que_revienta_va_a_cuarentena_sin_abortar(monkeypatch, tmp_path):
    hojas = {
        "31032020": HojaFalsa(celdas_validas()),
        "30032020": RuntimeError("BIFF corrupto en esta hoja"),
    }
    resultado = parsear(monkeypatch, tmp_path, hojas)
    assert len(resultado.jornadas) == 1  # la hoja sana se carga (RF06)
    descarte = resultado.descartes[0]
    assert descarte.hoja == "30032020"
    assert "ilegible" in descarte.motivo
