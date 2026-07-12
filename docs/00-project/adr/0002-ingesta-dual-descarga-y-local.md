# ADR-0002: Ingesta dual — descarga del portal BCV + carpeta local, pipeline único

* **Estado:** accepted
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 1.1.0
* **ID:** ADR-0002
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A02 (comunicaciones), A08 (integridad)

## Contexto

RF01/RF02: el usuario decidió soportar ambas fuentes — descarga automática desde bcv.org.ve y archivos colocados manualmente (históricos ya descargados, correcciones). Dos fuentes no deben significar dos pipelines con validaciones divergentes.

## Decisión

Un único pipeline de ingesta (hash → parseo → validación → carga) detrás del puerto `FuenteArchivosPort`, con dos adaptadores: `DescargadorHttpBcv` y `CarpetaLocalAdapter`. Todo archivo, venga de donde venga, es entrada no confiable: mismo hash SHA-256, mismas validaciones, misma cuarentena. El origen (`descarga`/`local`) se registra en `ingesta.origen`.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| Pipeline único, dos adaptadores (elegida) | Validación uniforme, un solo código que auditar | Adaptador HTTP añade dependencia (httpx) | Uniforme y bajo |
| Solo carpeta local | Sin superficie de red | Trabajo manual recurrente para el operador | Menor superficie, mayor error humano |
| Solo descarga automática | Menos pasos manuales | Sin vía para históricos no publicados o correcciones | Dependencia total del portal (T8) |
| Dos pipelines separados | Independencia | Validaciones divergen con el tiempo → T1/T3 se cuelan por la vía menos mantenida | Alto |

## Consecuencias

- Positivas: idempotencia y validación idénticas para ambas vías; T4 cubierto por hash único global.
- Negativas / deuda asumida: el patrón de URLs históricas del BCV puede romperse sin aviso. Patrón confirmado el 2026-07-11: `https://www.bcv.org.ve/sites/default/files/EstadisticasGeneral/2_1_2{t}{AA}_smc.xls` (`{t}`: `a`–`d` = trimestre I–IV; `{AA}`: año en dos dígitos); histórico publicado desde 2020-TI, períodos inexistentes responden HTTP 404.
- Impacto en threat model: concentra T2 en un solo adaptador auditable; el modo local es mitigación de T8.
