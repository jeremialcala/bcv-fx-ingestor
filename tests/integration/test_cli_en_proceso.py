"""La CLI invocada en proceso: mismas aserciones que el e2e, con cobertura medible."""
import json

import pytest

from bcv_ingest import cli
from bcv_ingest.adaptadores.integridad import sha256_de
from bcv_ingest.cli import main
from bcv_ingest.dominio.modelos import ArchivoSmc, ErrorDescarga, OrigenArchivo, Periodo


def ejecutar(capsys, *argumentos):
    codigo = main(list(argumentos))
    return codigo, json.loads(capsys.readouterr().out)


def test_flujo_cargar_reingesta_y_estado(tmp_path, fixture_smc, capsys):
    db = str(tmp_path / "fx.db")

    codigo, resumenes = ejecutar(capsys, "--db", db, "cargar", str(fixture_smc))
    assert codigo == 2
    assert resumenes[0]["estado"] == "cargado_parcial"
    assert resumenes[0]["jornadas_cargadas"] == 3
    assert resumenes[0]["tasas_cargadas"] == 68

    codigo, resumenes = ejecutar(capsys, "--db", db, "cargar", str(fixture_smc))
    assert codigo == 0
    assert resumenes[0]["estado"] == "duplicado"

    codigo, estado = ejecutar(capsys, "--db", db, "estado")
    assert codigo == 0
    assert estado["totales"] == {"jornadas": 3, "tasas": 68, "cuarentenas_pendientes": 1}

    codigo, estado = ejecutar(capsys, "--db", db, "estado", "--jornada", "2020-03-31")
    assert codigo == 0
    assert estado["jornada"]["tasas"] == 22


def test_cargar_carpeta_completa(tmp_path, fixture_smc, capsys):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / fixture_smc.name).write_bytes(fixture_smc.read_bytes())
    (entrada / "corrupto.xls").write_text("no soy un XLS")

    codigo, resumenes = ejecutar(capsys, "--db", str(tmp_path / "fx.db"), "cargar", str(entrada))
    assert codigo == 2
    estados = {r["archivo"]: r["estado"] for r in resumenes}
    assert estados["2_1_2a20_smc.xls"] == "cargado_parcial"
    assert estados["corrupto.xls"] == "cuarentena"  # RF06: el lote no se aborta


def test_descargar_ingiere_y_reporta_no_publicados(tmp_path, fixture_smc, capsys, monkeypatch):
    # contrato del comando descargar sin tocar la red: solo 2020-TI "publicado"
    class DescargadorFalso:
        def __init__(self, destino):
            pass

        def obtener(self, periodo=None):
            if periodo == Periodo(2020, 1):
                yield ArchivoSmc(
                    ruta=fixture_smc, sha256=sha256_de(fixture_smc), origen=OrigenArchivo.DESCARGA
                )

    monkeypatch.setattr(cli, "DescargadorHttpBcv", DescargadorFalso)
    codigo, resultados = ejecutar(
        capsys, "--db", str(tmp_path / "fx.db"),
        "descargar", "--desde", "2020-01", "--hasta", "2020-06",
    )
    assert codigo == 2  # la cuarentena CHF manda exit 2
    estados = {r["periodo"]: r["estado"] for r in resultados}
    assert estados == {"2020-TI": "cargado_parcial", "2020-TII": "no_publicado"}


def test_descargar_con_fallo_de_red_sale_con_3(tmp_path, capsys, monkeypatch):
    class DescargadorRoto:
        def __init__(self, destino):
            pass

        def obtener(self, periodo=None):
            raise ErrorDescarga("fallo de red o TLS simulado")

    monkeypatch.setattr(cli, "DescargadorHttpBcv", DescargadorRoto)
    codigo, salida = ejecutar(
        capsys, "--db", str(tmp_path / "fx.db"),
        "descargar", "--desde", "2020-01", "--hasta", "2020-03",
    )
    assert codigo == 3  # contrato: error de red
    assert "fallo de red" in salida["error"]


def test_ruta_inexistente_sale_con_2(tmp_path):
    with pytest.raises(SystemExit) as salida:
        main(["--db", str(tmp_path / "fx.db"), "cargar", "no-existe.xls"])
    assert salida.value.code == 2


def test_mes_invalido_sale_con_2(tmp_path):
    with pytest.raises(SystemExit) as salida:
        main(["--db", str(tmp_path / "fx.db"), "descargar", "--desde", "2020-13", "--hasta", "2020-12"])
    assert salida.value.code == 2


def test_jornada_invalida_sale_con_2(tmp_path):
    with pytest.raises(SystemExit) as salida:
        main(["--db", str(tmp_path / "fx.db"), "estado", "--jornada", "31/03/2020"])
    assert salida.value.code == 2
