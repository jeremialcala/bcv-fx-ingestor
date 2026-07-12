from datetime import date, datetime
from pathlib import Path

import pytest

from bcv_ingest.adaptadores import lector_xls
from bcv_ingest.adaptadores.lector_xls import LectorXlsXlrd
from bcv_ingest.dominio.modelos import ArchivoIlegibleError, ArchivoSmc, OrigenArchivo


def archivo(ruta: Path) -> ArchivoSmc:
    return ArchivoSmc(ruta=ruta, sha256="irrelevante", origen=OrigenArchivo.LOCAL)


def test_parsea_el_archivo_real_completo(fixture_smc):
    resultado = LectorXlsXlrd().parsear(archivo(fixture_smc))

    assert resultado.descartes == ()
    assert len(resultado.jornadas) == 3
    por_fecha = {j.fecha_operacion: j for j in resultado.jornadas}
    assert set(por_fecha) == {date(2020, 3, 27), date(2020, 3, 30), date(2020, 3, 31)}
    assert all(len(j.tasas) == 23 for j in resultado.jornadas)

    ultima = por_fecha[date(2020, 3, 31)]
    assert ultima.fecha_valor == date(2020, 4, 1)
    assert ultima.publicado_en == datetime(2020, 3, 31, 15, 49)

    chf = next(t for t in ultima.tasas if t.codigo_moneda == "CHF")
    assert chf.usd_bid == 0.96273
    assert chf.usd_ask == 9.96296  # la anomalía real llega cruda; la juzga el Validador

    usd = next(t for t in ultima.tasas if t.codigo_moneda == "USD")
    assert usd.bs_bid == pytest.approx(80743.36018875)


def test_archivo_no_xls_es_ilegible(tmp_path):
    falso = tmp_path / "falso.xls"
    falso.write_text("esto no es un XLS BIFF")
    with pytest.raises(ArchivoIlegibleError):
        LectorXlsXlrd().parsear(archivo(falso))


def test_limite_de_tamano_rs02(fixture_smc, monkeypatch):
    monkeypatch.setattr(lector_xls, "LIMITE_BYTES", 1024)
    with pytest.raises(ArchivoIlegibleError, match="límite"):
        LectorXlsXlrd().parsear(archivo(fixture_smc))
