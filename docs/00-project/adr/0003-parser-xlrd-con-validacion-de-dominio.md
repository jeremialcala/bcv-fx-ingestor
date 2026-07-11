# ADR-0003: Parser xlrd con contrato de layout y validación de dominio

* **Estado:** accepted
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0003
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A03 (entrada no confiable), A08 (integridad)

## Contexto

Los archivos SMC son `.xls` legacy (BIFF/Excel 97-2003, formato OLE2). RF03/RF04 exigen parsear un layout posicional (cabecera en filas 0–9, monedas desde fila 10, notas al pie) y validar contra errores reales de la fuente (CHF 31/03/2020: BID 0.96273, ASK 9.96296 — factor ~10 de error). T1 (cambio de layout) es la amenaza mejor puntuada del DREAD.

## Decisión

`xlrd` (única librería madura para `.xls` BIFF en Python) envuelta en el adaptador `LectorXlsXlrd`, con un **contrato de layout explícito**: antes de extraer datos se verifican anclas (título "TIPO DE CAMBIO DE REFERENCIA", encabezados "Moneda/País", "Compra (BID)", "Venta (ASK)", patrón `DDMMYYYY` del nombre de hoja). Si un ancla no coincide, la hoja va a cuarentena completa — nunca extracción "a mejor esfuerzo". La validación de dominio (BID≤ASK, positivos, moneda en catálogo, fecha_valor≥fecha_operacion) vive en el Validador, fuera del adaptador.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| xlrd + contrato de anclas (elegida) | Soporta BIFF real; falla cerrado ante layout distinto | xlrd sin desarrollo activo (congelado para .xls) | Parser legacy: mitigar con límites y no-privilegios |
| pandas.read_excel | API cómoda | Usa xlrd por debajo para .xls; oculta el layout posicional y las anclas | Igual + extracción implícita "mejor esfuerzo" (alimenta T1) |
| LibreOffice headless → CSV | Robusto ante variantes | Dependencia pesada externa al stack; conversión no auditable | Superficie mayor |
| Parser BIFF propio | Control total | Costo desproporcionado | Alto (bugs propios) |

## Consecuencias

- Positivas: T1 y T3 tienen control directo y testeable; el caso CHF es el test de aceptación natural de RF04.
- Negativas / deuda asumida: dependencia congelada (xlrd); si el BCV migra a `.xlsx`, se añade un segundo adaptador (openpyxl) tras el mismo puerto.
- Impacto en threat model: reduce probabilidad de T1; T5 permanece y se mitiga con límites de tamaño/filas y ejecución sin privilegios.
