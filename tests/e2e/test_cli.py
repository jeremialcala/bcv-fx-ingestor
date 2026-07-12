"""E2E: la CLI real contra el archivo oficial del BCV (escenarios E2/E3 del PRD)."""
import json
import subprocess
import sys


def bcv_ingest(tmp_path, *argumentos):
    proceso = subprocess.run(
        [sys.executable, "-m", "bcv_ingest.cli", *argumentos],
        capture_output=True, text=True, encoding="utf-8", cwd=tmp_path,
    )
    return proceso.returncode, json.loads(proceso.stdout)


def test_cargar_estado_y_reingesta(tmp_path, fixture_smc):
    # E2: cargar el archivo real → 3 jornadas, 68 tasas (69 filas − CHF en cuarentena)
    codigo, resumenes = bcv_ingest(tmp_path, "cargar", str(fixture_smc))
    assert codigo == 2  # hubo cuarentenas
    assert len(resumenes) == 1
    resumen = resumenes[0]
    assert resumen["estado"] == "cargado_parcial"
    assert resumen["jornadas_cargadas"] == 3
    assert resumen["tasas_cargadas"] == 68
    assert resumen["duplicadas"] == 0
    assert len(resumen["cuarentenas"]) == 1
    assert "CHF" in resumen["cuarentenas"][0]["motivo"]
    assert resumen["cuarentenas"][0]["hoja"] == "31032020"

    # E3: re-ingesta → duplicado por hash, 0 filas nuevas, exit 0
    codigo, resumenes = bcv_ingest(tmp_path, "cargar", str(fixture_smc))
    assert codigo == 0
    assert resumenes[0]["estado"] == "duplicado"
    assert resumenes[0]["jornadas_cargadas"] == 0

    # estado general: totales y cuarentena pendiente visibles (RF08)
    codigo, estado = bcv_ingest(tmp_path, "estado")
    assert codigo == 0
    assert estado["totales"] == {"jornadas": 3, "tasas": 68, "cuarentenas_pendientes": 1}
    assert estado["ingestas"][0]["estado"] == "cargado_parcial"

    # estado por jornada: el 31/03 cargó 22 tasas (CHF quedó fuera) y muestra su cuarentena
    codigo, estado = bcv_ingest(tmp_path, "estado", "--jornada", "2020-03-31")
    assert codigo == 0
    assert estado["jornada"]["tasas"] == 22
    assert estado["jornada"]["escala_monetaria"] == 10**6
    assert len(estado["cuarentenas"]) == 1


def test_cargar_archivo_corrupto_va_a_cuarentena(tmp_path):
    corrupto = tmp_path / "2_1_2x99_smc.xls"
    corrupto.write_text("no soy un XLS")
    codigo, resumenes = bcv_ingest(tmp_path, "cargar", str(corrupto))
    assert codigo == 2
    assert resumenes[0]["estado"] == "cuarentena"
    assert resumenes[0]["jornadas_cargadas"] == 0


def test_ruta_inexistente_es_error_de_uso(tmp_path):
    proceso = subprocess.run(
        [sys.executable, "-m", "bcv_ingest.cli", "cargar", "no-existe.xls"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert proceso.returncode == 2
