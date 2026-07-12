"""Validador de dominio (RF04): decide qué filas se cargan y cuáles van a cuarentena.

Regla de coherencia entre bases (refinamiento de RF04, 2026-07-12): en el caso real
CHF 31/03/2020 el error de la fuente (ASK 9.96296 por 0.96296) cumple BID<=ASK, pero
el spread de la base M.E./US$ (~10x) es incoherente con el de la base Bs./M.E. (~0,25%)
de la misma fila. Se comparan ambos spreads como razón multiplicativa y una divergencia
mayor al umbral envía la fila a cuarentena.

Umbral calibrado contra el corpus real 2020-2026: hay monedas con spread legítimo ancho
y estable — ANG cotiza en banda ~5,3% desde 2023, BOB ~5,6% en 2024-2025 — cuya
divergencia máxima observada entre bases es 1.058; el error real más pequeño observado
(CHF, dígito corrido) diverge 10.35. El umbral 1.25 deja margen amplio hacia ambos lados.
"""
from __future__ import annotations

import json

from .modelos import ItemCuarentena, JornadaCruda, JornadaValidada, TasaCruda, TasaValidada
from .monedas import CATALOGO
from .redenominaciones import escala_para

DIVERGENCIA_MAXIMA_SPREAD = 1.25


class ValidadorDominio:
    def validar(
        self, jornada: JornadaCruda
    ) -> tuple[JornadaValidada | None, list[ItemCuarentena]]:
        """Devuelve la jornada con sus tasas válidas (o None) y los items de cuarentena."""
        if jornada.fecha_valor < jornada.fecha_operacion:
            return None, [
                ItemCuarentena(
                    hoja=jornada.hoja,
                    motivo=(
                        f"fecha_valor {jornada.fecha_valor.isoformat()} anterior a "
                        f"fecha_operacion {jornada.fecha_operacion.isoformat()}"
                    ),
                )
            ]

        cuarentena: list[ItemCuarentena] = []
        validas: list[TasaValidada] = []
        for tasa in jornada.tasas:
            motivo = self._validar_tasa(tasa)
            if motivo:
                cuarentena.append(
                    ItemCuarentena(
                        hoja=jornada.hoja,
                        motivo=f"{tasa.codigo_moneda}: {motivo}",
                        payload_crudo=_payload(tasa),
                    )
                )
                continue
            validas.append(
                TasaValidada(
                    codigo_moneda=tasa.codigo_moneda,
                    usd_bid=tasa.usd_bid,
                    usd_ask=tasa.usd_ask,
                    bs_bid=tasa.bs_bid,
                    bs_ask=tasa.bs_ask,
                    cotizacion_invertida=CATALOGO[tasa.codigo_moneda].cotizacion_invertida,
                )
            )

        if not validas:
            cuarentena.append(
                ItemCuarentena(hoja=jornada.hoja, motivo="hoja sin tasas válidas")
            )
            return None, cuarentena

        return (
            JornadaValidada(
                fecha_operacion=jornada.fecha_operacion,
                fecha_valor=jornada.fecha_valor,
                publicado_en=jornada.publicado_en,
                escala_monetaria=escala_para(jornada.fecha_operacion),
                tasas=tuple(validas),
            ),
            cuarentena,
        )

    def _validar_tasa(self, tasa: TasaCruda) -> str | None:
        valores = (tasa.usd_bid, tasa.usd_ask, tasa.bs_bid, tasa.bs_ask)
        if any(v is None for v in valores):
            return "valor ausente o no numérico"
        if any(v <= 0 for v in valores):
            return "valor no positivo"
        if tasa.codigo_moneda not in CATALOGO:
            return "moneda fuera del catálogo"
        if tasa.usd_bid > tasa.usd_ask or tasa.bs_bid > tasa.bs_ask:
            return "BID mayor que ASK"
        spread_usd = tasa.usd_ask / tasa.usd_bid
        spread_bs = tasa.bs_ask / tasa.bs_bid
        divergencia = max(spread_usd, spread_bs) / min(spread_usd, spread_bs)
        if divergencia > DIVERGENCIA_MAXIMA_SPREAD:
            return (
                f"spread BID/ASK incoherente entre bases (divergencia {divergencia:.2f}x; "
                f"M.E./US$: {spread_usd:.4f}, Bs./M.E.: {spread_bs:.4f}) — posible error de la fuente"
            )
        return None


def _payload(tasa: TasaCruda) -> str:
    return json.dumps(
        {
            "codigo_moneda": tasa.codigo_moneda,
            "pais": tasa.pais,
            "usd_bid": tasa.usd_bid,
            "usd_ask": tasa.usd_ask,
            "bs_bid": tasa.bs_bid,
            "bs_ask": tasa.bs_ask,
            "fila": tasa.fila,
        },
        ensure_ascii=False,
    )
