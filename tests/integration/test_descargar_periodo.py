"""Caso de uso DescargarPeriodo con una fuente simulada y el pipeline real (RF01)."""
from pathlib import Path

from bcv_ingest.adaptadores.integridad import sha256_de
from bcv_ingest.adaptadores.lector_xls import LectorXlsXlrd
from bcv_ingest.adaptadores.repositorio_sqlite import RepositorioSqlite
from bcv_ingest.aplicacion.descargar_periodo import DescargarPeriodoUseCase
from bcv_ingest.aplicacion.ingestar_archivo import IngestarArchivoUseCase
from bcv_ingest.dominio.modelos import ArchivoSmc, OrigenArchivo, Periodo
from bcv_ingest.dominio.puertos import FuenteArchivosPort
from bcv_ingest.dominio.validador import ValidadorDominio


class FuenteSimulada(FuenteArchivosPort):
    """Simula el portal: solo publica 2020-TI, como el histórico real más antiguo."""

    def __init__(self, ruta_publicada: Path):
        self._ruta = ruta_publicada

    def obtener(self, periodo=None):
        if periodo == Periodo(2020, 1):
            yield ArchivoSmc(
                ruta=self._ruta, sha256=sha256_de(self._ruta), origen=OrigenArchivo.DESCARGA
            )


def caso_de_uso(tmp_path, fixture_smc):
    repositorio = RepositorioSqlite(tmp_path / "fx.db")
    ingestar = IngestarArchivoUseCase(LectorXlsXlrd(), ValidadorDominio(), repositorio)
    return DescargarPeriodoUseCase(FuenteSimulada(fixture_smc), ingestar, repositorio)


def test_rango_con_periodo_no_publicado_e_ingesta(tmp_path, fixture_smc):
    resultados = caso_de_uso(tmp_path, fixture_smc).ejecutar(Periodo(2019, 4), Periodo(2020, 1))

    por_periodo = {r["periodo"]: r for r in resultados}
    assert por_periodo["2019-TIV"]["estado"] == "no_publicado"
    assert por_periodo["2020-TI"]["estado"] == "cargado_parcial"
    assert por_periodo["2020-TI"]["origen"] == "descarga"
    assert por_periodo["2020-TI"]["jornadas_cargadas"] == 3


def test_no_redescarga_lo_ya_ingerido_rf01(tmp_path, fixture_smc):
    caso = caso_de_uso(tmp_path, fixture_smc)
    caso.ejecutar(Periodo(2020, 1), Periodo(2020, 1))

    segunda = caso.ejecutar(Periodo(2020, 1), Periodo(2020, 1))
    assert segunda[0]["estado"] == "omitido_ya_ingerido"

    forzada = caso.ejecutar(Periodo(2020, 1), Periodo(2020, 1), forzar=True)
    assert forzada[0]["estado"] == "duplicado"  # mismo hash: no se re-procesa
