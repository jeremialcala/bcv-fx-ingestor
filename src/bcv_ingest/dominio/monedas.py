"""Catálogo de monedas del Archivo SMC (RF04: solo códigos conocidos se cargan).

EUR y GBP cotizan invertidas: US$ por M.E. en vez de M.E. por US$ (nota (a) del archivo).
MXP y CUC no son códigos ISO 4217 vigentes, pero son los que publica el BCV.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Moneda:
    codigo: str
    pais: str
    es_iso4217: bool = True
    cotizacion_invertida: bool = False


CATALOGO: dict[str, Moneda] = {
    m.codigo: m
    for m in (
        Moneda("EUR", "Zona Euro", cotizacion_invertida=True),
        Moneda("CNY", "China"),
        Moneda("TRY", "Turquía"),
        Moneda("RUB", "Rusia"),
        Moneda("USD", "E.U.A."),
        Moneda("GBP", "Reino Unido", cotizacion_invertida=True),
        Moneda("CAD", "Canadá"),
        Moneda("INR", "India"),
        Moneda("CHF", "Suiza"),
        Moneda("JPY", "Japón"),
        Moneda("ARS", "Argentina"),
        Moneda("BRL", "Brasil"),
        Moneda("CLP", "Chile"),
        Moneda("COP", "Colombia"),
        Moneda("UYU", "Uruguay"),
        Moneda("PEN", "Perú"),
        Moneda("BOB", "Bolivia"),
        Moneda("MXP", "México", es_iso4217=False),
        Moneda("CUC", "Cuba", es_iso4217=False),
        Moneda("NIO", "Nicaragua"),
        Moneda("DOP", "República Dominicana"),
        Moneda("TTD", "Trinidad y Tobago"),
        Moneda("ANG", "Curazao"),
    )
}
