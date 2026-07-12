import pytest

from bcv_ingest.dominio.modelos import Periodo


def test_desde_mes_asigna_trimestre():
    assert Periodo.desde_mes("2020-01") == Periodo(2020, 1)
    assert Periodo.desde_mes("2020-03") == Periodo(2020, 1)
    assert Periodo.desde_mes("2020-04") == Periodo(2020, 2)
    assert Periodo.desde_mes("2026-07") == Periodo(2026, 3)
    assert Periodo.desde_mes("2026-12") == Periodo(2026, 4)


def test_nombre_archivo_sigue_el_patron_confirmado():
    assert Periodo(2020, 1).nombre_archivo == "2_1_2a20_smc.xls"
    assert Periodo(2026, 3).nombre_archivo == "2_1_2c26_smc.xls"
    assert Periodo(2025, 4).nombre_archivo == "2_1_2d25_smc.xls"


def test_rango_cruza_anios():
    periodos = Periodo.rango(Periodo(2020, 3), Periodo(2021, 2))
    assert periodos == [Periodo(2020, 3), Periodo(2020, 4), Periodo(2021, 1), Periodo(2021, 2)]


def test_rango_de_un_solo_trimestre():
    assert Periodo.rango(Periodo(2020, 1), Periodo(2020, 1)) == [Periodo(2020, 1)]


def test_rango_invertido_es_error():
    with pytest.raises(ValueError):
        Periodo.rango(Periodo(2021, 1), Periodo(2020, 4))


@pytest.mark.parametrize("texto", ["2020", "2020-13", "2020-00", "20-01", "enero 2020"])
def test_mes_invalido_es_error(texto):
    with pytest.raises(ValueError):
        Periodo.desde_mes(texto)


def test_trimestre_fuera_de_rango_es_error():
    with pytest.raises(ValueError):
        Periodo(2020, 5)
