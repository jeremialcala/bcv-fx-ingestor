"""Tabla de vigencia de redenominaciones del bolívar (RF07, amenaza T7).

`escala_monetaria` es el divisor que lleva un monto en bolívares de la época de la
jornada al bolívar vigente (Bs.D, desde 2021-10-01):

- 2018-08-20: Bs.S = 100.000 Bs.F  (factor 10^5)
- 2021-10-01: Bs.D = 1.000.000 Bs.S (factor 10^6; acumulado pre-2018: 10^11)
"""
from datetime import date

# (fecha de entrada en vigencia, divisor acumulado hacia el bolívar actual)
VIGENCIAS: tuple[tuple[date, int], ...] = (
    (date(2021, 10, 1), 1),
    (date(2018, 8, 20), 10**6),
    (date.min, 10**11),
)


def escala_para(fecha_operacion: date) -> int:
    for inicio, escala in VIGENCIAS:
        if fecha_operacion >= inicio:
            return escala
    raise AssertionError("VIGENCIAS debe cubrir cualquier fecha")
