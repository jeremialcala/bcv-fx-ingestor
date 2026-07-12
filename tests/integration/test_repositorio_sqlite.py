from datetime import date, datetime
from pathlib import Path

import pytest

from bcv_ingest.adaptadores.repositorio_sqlite import RepositorioSqlite
from bcv_ingest.dominio.modelos import (
    ArchivoSmc,
    EstadoIngesta,
    ItemCuarentena,
    JornadaValidada,
    OrigenArchivo,
    TasaValidada,
)


@pytest.fixture
def repo(tmp_path):
    repositorio = RepositorioSqlite(tmp_path / "test.db")
    yield repositorio
    repositorio.cerrar()


def archivo(sha="a" * 64):
    return ArchivoSmc(
        ruta=Path("2_1_2a20_smc.xls"), sha256=sha, origen=OrigenArchivo.LOCAL
    )


def jornada():
    return JornadaValidada(
        fecha_operacion=date(2020, 3, 31),
        fecha_valor=date(2020, 4, 1),
        publicado_en=datetime(2020, 3, 31, 15, 49),
        escala_monetaria=10**6,
        tasas=(
            TasaValidada("USD", 1.0, 1.0, 80743.36, 80945.72, False),
            TasaValidada("EUR", 1.10127, 1.10131, 88923.47, 89146.33, True),
        ),
    )


def test_guardar_jornada_es_idempotente_rf05(repo):
    ingesta_id = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)

    primera = repo.guardar_jornada(jornada(), ingesta_id)
    assert primera.jornada_nueva is True
    assert primera.tasas_nuevas == 2
    assert primera.tasas_duplicadas == 0

    segunda = repo.guardar_jornada(jornada(), ingesta_id)
    assert segunda.jornada_nueva is False
    assert segunda.tasas_nuevas == 0
    assert segunda.tasas_duplicadas == 2  # re-ingesta no crea filas (métrica del PRD)


def test_hash_conocido_solo_para_ingestas_cargadas(repo):
    ingesta_id = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)
    assert repo.hash_conocido(archivo().sha256) is False

    repo.actualizar_estado(ingesta_id, EstadoIngesta.CARGADO)
    repo.confirmar()
    assert repo.hash_conocido(archivo().sha256) is True
    assert repo.nombre_archivo_ingerido("2_1_2a20_smc.xls") is True


def test_reproceso_tras_cuarentena_reutiliza_la_ingesta(repo):
    # ciclo del stateDiagram: Cuarentena -> Validando tras decisión humana
    primero = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)
    repo.enviar_a_cuarentena(primero, ItemCuarentena(hoja="31032020", motivo="layout roto"))
    repo.actualizar_estado(primero, EstadoIngesta.CUARENTENA)
    repo.confirmar()
    assert repo.hash_conocido(archivo().sha256) is False  # puede reprocesarse

    segundo = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)
    assert segundo == primero
    assert repo.estado_general()["totales"]["cuarentenas_pendientes"] == 0  # limpiada


def test_cuarentena_con_contenido_hostil_no_inyecta_sql(repo):
    # A5: el contenido de celdas jamás se concatena en SQL
    ingesta_id = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)
    hostil = "'; DROP TABLE tasa;--"
    repo.enviar_a_cuarentena(ingesta_id, ItemCuarentena(hoja=None, motivo=hostil))
    repo.confirmar()

    estado = repo.estado_general()
    assert estado["cuarentenas"][0]["motivo"] == hostil
    assert estado["totales"]["tasas"] == 0  # la tabla sigue existiendo y vacía


def test_estado_general_filtra_por_jornada(repo):
    ingesta_id = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)
    repo.guardar_jornada(jornada(), ingesta_id)
    repo.enviar_a_cuarentena(
        ingesta_id, ItemCuarentena(hoja="31032020", motivo="CHF: spread incoherente")
    )
    repo.enviar_a_cuarentena(
        ingesta_id, ItemCuarentena(hoja="30032020", motivo="otra cosa")
    )
    repo.actualizar_estado(ingesta_id, EstadoIngesta.CARGADO_PARCIAL)
    repo.confirmar()

    estado = repo.estado_general(date(2020, 3, 31))
    assert estado["jornada"]["tasas"] == 2
    assert estado["jornada"]["escala_monetaria"] == 10**6
    assert [c["motivo"] for c in estado["cuarentenas"]] == ["CHF: spread incoherente"]


def test_revertir_descarta_la_transaccion_completa(repo):
    # A1: nunca cargas parciales
    ingesta_id = repo.registrar_ingesta(archivo(), EstadoIngesta.VALIDANDO)
    repo.guardar_jornada(jornada(), ingesta_id)
    repo.revertir()

    estado = repo.estado_general()
    assert estado["ingestas"] == []
    assert estado["totales"]["jornadas"] == 0
