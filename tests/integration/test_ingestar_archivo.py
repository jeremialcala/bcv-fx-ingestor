"""Matriz de transición de estados de la Ingesta (Gate 3): las transiciones del
stateDiagram que la pirámide no cubría — Cargado limpio, Fallido con rollback,
reproceso de Cuarentena y re-ingesta alterada (A4)."""
import logging
from datetime import date, datetime
from pathlib import Path

import pytest

from bcv_ingest.adaptadores.lector_xls import LectorXlsXlrd
from bcv_ingest.adaptadores.repositorio_sqlite import RepositorioSqlite
from bcv_ingest.aplicacion.ingestar_archivo import IngestarArchivoUseCase
from bcv_ingest.dominio.modelos import ArchivoSmc, JornadaCruda, OrigenArchivo, TasaCruda
from bcv_ingest.dominio.puertos import LectorTasasPort, ResultadoParseo
from bcv_ingest.dominio.validador import ValidadorDominio


class LectorFalso(LectorTasasPort):
    def __init__(self, jornadas):
        self._jornadas = tuple(jornadas)

    def parsear(self, archivo):
        return ResultadoParseo(jornadas=self._jornadas, descartes=())


def jornada_limpia(fecha=date(2020, 3, 31)):
    return JornadaCruda(
        hoja=fecha.strftime("%d%m%Y"),
        fecha_operacion=fecha,
        fecha_valor=date(2020, 4, 1),
        publicado_en=datetime(2020, 3, 31, 15, 49),
        tasas=(
            TasaCruda("USD", "E.U.A.", 1.0, 1.0, 80743.36, 80945.72, fila=14),
            TasaCruda("EUR", "Zona Euro", 1.10127, 1.10131, 88923.47, 89146.33, fila=10),
        ),
    )


def archivo(nombre="2_1_2a20_smc.xls", sha="a" * 64):
    return ArchivoSmc(ruta=Path(nombre), sha256=sha, origen=OrigenArchivo.LOCAL)


@pytest.fixture
def repo(tmp_path):
    repositorio = RepositorioSqlite(tmp_path / "fx.db")
    yield repositorio
    repositorio.cerrar()


def test_transicion_validando_a_cargado(repo):
    caso = IngestarArchivoUseCase(LectorFalso([jornada_limpia()]), ValidadorDominio(), repo)
    resumen = caso.ejecutar(archivo())
    assert resumen.estado == "cargado"
    assert resumen.jornadas_cargadas == 1
    assert resumen.tasas_cargadas == 2
    assert resumen.cuarentenas == []


def test_transicion_a_fallido_revierte_todo(repo, monkeypatch):
    # A1: un error inesperado a mitad de carga no deja filas parciales
    caso = IngestarArchivoUseCase(LectorFalso([jornada_limpia()]), ValidadorDominio(), repo)

    def explota(jornada, ingesta_id):
        raise RuntimeError("disco lleno")

    monkeypatch.setattr(repo, "guardar_jornada", explota)
    with pytest.raises(RuntimeError):
        caso.ejecutar(archivo())

    estado = repo.estado_general()
    assert [i["estado"] for i in estado["ingestas"]] == ["fallido"]
    assert estado["totales"]["jornadas"] == 0  # rollback completo


def test_reproceso_de_cuarentena_no_acumula_items(repo, tmp_path):
    # ciclo Cuarentena -> Validando: reintentar el mismo archivo no duplica cuarentenas
    corrupto = tmp_path / "2_1_2x99_smc.xls"
    corrupto.write_text("no soy un XLS")
    caso = IngestarArchivoUseCase(LectorXlsXlrd(), ValidadorDominio(), repo)
    archivo_corrupto = ArchivoSmc(ruta=corrupto, sha256="b" * 64, origen=OrigenArchivo.LOCAL)

    primero = caso.ejecutar(archivo_corrupto)
    segundo = caso.ejecutar(archivo_corrupto)

    assert primero.estado == segundo.estado == "cuarentena"
    estado = repo.estado_general()
    assert estado["totales"]["cuarentenas_pendientes"] == 1
    assert len(estado["ingestas"]) == 1


def test_reingesta_alterada_no_sobreescribe_a4(repo):
    # A4/T4: mismo nombre y mismas jornadas pero contenido alterado (hash distinto):
    # se procesa como ingesta nueva, no crea filas ni roba la trazabilidad original
    validador = ValidadorDominio()
    original = IngestarArchivoUseCase(LectorFalso([jornada_limpia()]), validador, repo)
    alterado = IngestarArchivoUseCase(LectorFalso([jornada_limpia()]), validador, repo)

    original.ejecutar(archivo(sha="c" * 64))
    resumen = alterado.ejecutar(archivo(sha="d" * 64))

    assert resumen.estado == "cargado"
    assert resumen.tasas_cargadas == 0
    assert resumen.duplicadas == 2  # nada se sobreescribe en silencio
    jornada = repo.estado_general(date(2020, 3, 31))["jornada"]
    assert jornada["tasas"] == 2  # sigue trazando a la ingesta original


def test_cuarentena_queda_auditada_en_logs_rs04(repo, fixture_smc, caplog):
    caso = IngestarArchivoUseCase(LectorXlsXlrd(), ValidadorDominio(), repo)
    with caplog.at_level(logging.WARNING, logger="bcv_ingest.aplicacion.ingestar_archivo"):
        caso.ejecutar(ArchivoSmc(ruta=fixture_smc, sha256="e" * 64, origen=OrigenArchivo.LOCAL))
    auditoria = [r.message for r in caplog.records if "cuarentena" in r.message]
    assert len(auditoria) == 1
    assert "2_1_2a20_smc.xls" in auditoria[0]
    assert "31032020" in auditoria[0]
    assert "CHF" in auditoria[0]
