from datetime import date, datetime

from bcv_ingest.dominio.modelos import JornadaCruda, TasaCruda
from bcv_ingest.dominio.validador import ValidadorDominio


def tasa(codigo="USD", usd_bid=1.0, usd_ask=1.0, bs_bid=80743.36, bs_ask=80945.72, pais="E.U.A."):
    return TasaCruda(
        codigo_moneda=codigo, pais=pais,
        usd_bid=usd_bid, usd_ask=usd_ask, bs_bid=bs_bid, bs_ask=bs_ask, fila=10,
    )


def jornada(tasas, fecha_operacion=date(2020, 3, 31), fecha_valor=date(2020, 4, 1)):
    return JornadaCruda(
        hoja=fecha_operacion.strftime("%d%m%Y"),
        fecha_operacion=fecha_operacion,
        fecha_valor=fecha_valor,
        publicado_en=datetime(2020, 3, 31, 15, 49),
        tasas=tuple(tasas),
    )


def test_fila_normal_se_carga():
    valida, cuarentena = ValidadorDominio().validar(jornada([tasa()]))
    assert cuarentena == []
    assert len(valida.tasas) == 1
    assert valida.tasas[0].codigo_moneda == "USD"
    assert valida.tasas[0].cotizacion_invertida is False


def test_caso_real_chf_31_03_2020_va_a_cuarentena():
    # valores exactos del archivo oficial: BID<=ASK se cumple (0.96273 <= 9.96296),
    # es la incoherencia de spreads entre bases lo que delata el error de la fuente
    chf = tasa(
        codigo="CHF", pais="Suiza",
        usd_bid=0.96273, usd_ask=9.96296,
        bs_bid=83869.16392835, bs_ask=84079.36233419,
    )
    valida, cuarentena = ValidadorDominio().validar(jornada([chf, tasa()]))
    assert len(cuarentena) == 1
    assert "CHF" in cuarentena[0].motivo
    assert "spread" in cuarentena[0].motivo
    assert cuarentena[0].payload_crudo is not None
    assert len(valida.tasas) == 1  # la fila sana de la misma hoja sí se carga (RF06)


def test_ang_con_banda_legitima_ancha_pasa():
    # caso real 06/07/2026: el florín de Curazao cotiza en banda oficial ~5,3%
    # estable desde 2023; no es un error de la fuente (501 falsos positivos con
    # la regla de diferencia absoluta que este umbral corrige)
    ang = tasa(codigo="ANG", pais="Curazao",
               usd_bid=1.7441, usd_ask=1.8363, bs_bid=386.01, bs_ask=386.98)
    valida, cuarentena = ValidadorDominio().validar(
        jornada([ang], fecha_operacion=date(2026, 7, 6), fecha_valor=date(2026, 7, 7))
    )
    assert cuarentena == []
    assert len(valida.tasas) == 1


def test_bob_con_spread_legitimo_ancho_pasa():
    # caso real 02/12/2024: spread ~5,7% sostenido por la escasez de divisas
    bob = tasa(codigo="BOB", pais="Bolivia",
               usd_bid=6.7168, usd_ask=7.0967, bs_bid=328.31, bs_ask=329.13)
    valida, cuarentena = ValidadorDominio().validar(
        jornada([bob], fecha_operacion=date(2024, 12, 2), fecha_valor=date(2024, 12, 3))
    )
    assert cuarentena == []
    assert len(valida.tasas) == 1


def test_chf_corregido_pasa():
    chf = tasa(codigo="CHF", usd_bid=0.96273, usd_ask=0.96296,
               bs_bid=83869.16, bs_ask=84079.36)
    valida, cuarentena = ValidadorDominio().validar(jornada([chf]))
    assert cuarentena == []
    assert len(valida.tasas) == 1


def test_bid_mayor_que_ask_va_a_cuarentena():
    _, cuarentena = ValidadorDominio().validar(jornada([tasa(usd_bid=1.2, usd_ask=1.1)]))
    assert any("BID mayor que ASK" in c.motivo for c in cuarentena)


def test_valor_no_positivo_va_a_cuarentena():
    _, cuarentena = ValidadorDominio().validar(jornada([tasa(bs_bid=0.0)]))
    assert any("no positivo" in c.motivo for c in cuarentena)


def test_valor_ausente_va_a_cuarentena():
    _, cuarentena = ValidadorDominio().validar(jornada([tasa(usd_ask=None)]))
    assert any("ausente" in c.motivo for c in cuarentena)


def test_moneda_desconocida_va_a_cuarentena():
    _, cuarentena = ValidadorDominio().validar(jornada([tasa(codigo="XXX")]))
    assert any("catálogo" in c.motivo for c in cuarentena)


def test_fecha_valor_anterior_a_operacion_descarta_la_hoja():
    valida, cuarentena = ValidadorDominio().validar(
        jornada([tasa()], fecha_operacion=date(2020, 4, 1), fecha_valor=date(2020, 3, 31))
    )
    assert valida is None
    assert any("fecha_valor" in c.motivo for c in cuarentena)


def test_hoja_sin_tasas_validas_queda_en_cuarentena():
    valida, cuarentena = ValidadorDominio().validar(jornada([tasa(usd_bid=-1.0)]))
    assert valida is None
    assert any("sin tasas válidas" in c.motivo for c in cuarentena)


def test_eur_y_gbp_se_marcan_invertidas():
    eur = tasa(codigo="EUR", pais="Zona Euro", usd_bid=1.10127, usd_ask=1.10131,
               bs_bid=88923.47, bs_ask=89146.33)
    valida, _ = ValidadorDominio().validar(jornada([eur]))
    assert valida.tasas[0].cotizacion_invertida is True


def test_escala_monetaria_por_fecha_de_jornada():
    valida, _ = ValidadorDominio().validar(jornada([tasa()]))
    assert valida.escala_monetaria == 10**6  # 2020: era del bolívar soberano
