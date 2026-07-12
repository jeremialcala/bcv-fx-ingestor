"""RNF01: un archivo trimestral (~65 hojas) en menos de 30 s (SLO del Gate 3).

Usa un archivo real del corpus descargado en `entrada/`; si no está (repo recién
clonado), el test se omite — la evidencia operativa queda en el gate 3.
"""
import time
from pathlib import Path

import pytest

from bcv_ingest.adaptadores.carpeta_local import CarpetaLocalAdapter
from bcv_ingest.adaptadores.lector_xls import LectorXlsXlrd
from bcv_ingest.adaptadores.repositorio_sqlite import RepositorioSqlite
from bcv_ingest.aplicacion.ingestar_archivo import IngestarArchivoUseCase
from bcv_ingest.dominio.validador import ValidadorDominio

ARCHIVO_TRIMESTRAL = Path(__file__).parents[2] / "entrada" / "2_1_2c25_smc.xls"


@pytest.mark.skipif(not ARCHIVO_TRIMESTRAL.exists(), reason="requiere el corpus descargado en entrada/")
def test_archivo_trimestral_bajo_el_slo_rnf01(tmp_path):
    repo = RepositorioSqlite(tmp_path / "perf.db")
    try:
        caso = IngestarArchivoUseCase(LectorXlsXlrd(), ValidadorDominio(), repo)
        archivo = next(CarpetaLocalAdapter(ARCHIVO_TRIMESTRAL).obtener())

        inicio = time.perf_counter()
        resumen = caso.ejecutar(archivo)
        duracion = time.perf_counter() - inicio

        assert resumen.jornadas_cargadas == 63
        assert duracion < 30.0, f"RNF01 violado: {duracion:.2f}s"
    finally:
        repo.cerrar()
