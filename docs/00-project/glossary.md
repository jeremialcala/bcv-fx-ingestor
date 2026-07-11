# Glosario / Lenguaje Ubicuo (DDD)

* **Estado:** approved
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 00-project
* **Versión:** 0.1.0
* **Contextos acotados:** Ingesta Cambiaria

| Término | Definición | Contexto acotado (Bounded Context) |
|---|---|---|
| Tipo de Cambio de Referencia | Tasa oficial producto de las operaciones en las mesas de cambio de los operadores cambiarios (art. 9, Convenio Cambiario N° 1; Resolución N° 19-05-01) | Ingesta Cambiaria |
| Archivo SMC | Archivo oficial `2_1_2{t}{AA}_smc.xls` publicado por el BCV con las tasas de referencia; uno por trimestre (`{t}`: `a`–`d` = trimestre I–IV, `{AA}`: año en dos dígitos), una hoja por fecha de operación | Ingesta Cambiaria |
| Jornada | Publicación de tasas de un día: fecha de operación + fecha valor + momento de publicación (una hoja del Archivo SMC) | Ingesta Cambiaria |
| Fecha de Operación | Día en que se transaron las operaciones que producen la tasa (nombre de la hoja, `DDMMYYYY`) | Ingesta Cambiaria |
| Fecha Valor | Día hábil siguiente en que la tasa aplica para liquidaciones | Ingesta Cambiaria |
| Cotización BID / ASK | Precio de compra (BID) y venta (ASK); el archivo la expresa en dos bases: M.E. por US$ y Bs. por M.E. | Ingesta Cambiaria |
| Cotización invertida | EUR y GBP se expresan en US$ por unidad de moneda (nota (a) del archivo), al revés del resto | Ingesta Cambiaria |
| Moneda | Divisa cotizada, identificada por código (ISO 4217 en general; excepciones no-ISO como `MXP` por peso mexicano) y país | Ingesta Cambiaria |
| Ingesta | Procesamiento de un Archivo SMC: obtención, validación, parseo y carga; entidad con ciclo de vida propio | Ingesta Cambiaria |
| Cuarentena | Estado de una ingesta o fila cuyos datos violan las reglas de validación; requiere decisión humana | Ingesta Cambiaria |
| Idempotencia | Propiedad de la carga: re-ingerir el mismo archivo o jornada no crea duplicados ni altera datos ya cargados | Ingesta Cambiaria |
| Redenominación | Cambio de escala del bolívar (Bs.F→Bs.S 2018 ÷100.000; Bs.S→Bs.D 2021 ÷1.000.000) que afecta la comparabilidad histórica | Ingesta Cambiaria |
| Mesa de Cambio | Mecanismo de los operadores cambiarios donde se transan las operaciones que originan la tasa | Ingesta Cambiaria |
