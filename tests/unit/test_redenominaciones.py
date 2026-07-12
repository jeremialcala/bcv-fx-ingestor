from datetime import date

from bcv_ingest.dominio.redenominaciones import escala_para


def test_bolivar_fuerte_antes_de_2018():
    assert escala_para(date(2018, 8, 19)) == 10**11
    assert escala_para(date(2010, 1, 1)) == 10**11


def test_bolivar_soberano_entre_redenominaciones():
    assert escala_para(date(2018, 8, 20)) == 10**6
    assert escala_para(date(2020, 3, 31)) == 10**6
    assert escala_para(date(2021, 9, 30)) == 10**6


def test_bolivar_digital_desde_2021():
    assert escala_para(date(2021, 10, 1)) == 1
    assert escala_para(date(2026, 7, 12)) == 1
