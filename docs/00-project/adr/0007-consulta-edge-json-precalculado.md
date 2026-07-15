# ADR-0007: Consulta en el edge vía JSON precalculado publicado junto al artefacto

* **Estado:** accepted
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0007
* **Supersede / Superseded-by:** supersede parcialmente ADR-0006 (el Worker deja de ser "solo distribución")
* **Controles OWASP afectados:** A01 (control de acceso), A03 (validación de entrada), A08 (integridad)

## Contexto

FX-ING-002 (Gate 0 aprobado 2026-07-14) requiere una API JSON de consulta y una Web UI en el Worker de Cloudflare: consulta puntual por fecha y moneda, serie por rango, última jornada y catálogo de monedas (RF09–RF12), con paridad exacta frente a SQL directo sobre el `.db` publicado (métrica de éxito del PRD). ADR-0006 estableció el Worker como "solo distribución" del artefacto; ese no-scope fue levantado en el Gate 0 del feature. El dataset es pequeño y de crecimiento lento: ~1.400 jornadas, ~31.000 tasas, 23 monedas, ~6.000 filas/año. Las formas de consulta son fijas y conocidas de antemano.

## Decisión

El pipeline de ingesta **precalcula la publicación como objetos JSON** derivados de SQLite y los publica en R2 junto al `.db`, en la misma corrida (misma fuente de verdad, publicación conjunta). El Worker **no ejecuta ningún motor de consulta**: resuelve cada endpoint leyendo el objeto R2 que corresponde y aplicando a lo sumo filtro/paginación en memoria.

Layout de publicación en R2 (prefijo `publicacion/`):

| Objeto | Contenido | Sirve a |
|---|---|---|
| `publicacion/ultima.json` | Última jornada con sus tasas | RF11 (`/api/jornadas/ultima`) |
| `publicacion/jornadas/AAAA-MM-DD.json` | Una jornada con sus tasas (~1.400 objetos) | RF09 (consulta puntual) |
| `publicacion/series/{MONEDA}.json` | Serie completa de una moneda (~1.400 filas, decenas de KB) | RF10 (rango; el Worker filtra y pagina) |
| `publicacion/monedas.json` | Catálogo de 23 monedas | RF12 |
| `publicacion/indice.json` | Fechas disponibles, `sha256` del `.db`, `generado_en` | RF17 (metadatos de frescura en toda respuesta) |

En el lado del ingestor, el núcleo gana el caso de uso `ExportarPublicacion` (nuevo puerto `ExportadorPublicacionPort` + adaptador de archivos JSON) y la CLI el comando `bcv-ingest exportar --destino DIR`; el CronJob lo ejecuta tras la ingesta y rclone sube `bcv_fx.db` + `publicacion/` en el mismo paso. Las filas en cuarentena **no** se exportan (paridad con el `.db`: la cuarentena nunca se publica).

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| JSON precalculado en R2 (elegida) | Sin motor SQL en el edge; misma fuente de verdad y publicación conjunta con el `.db`; costo y latencia mínimos; el Worker queda casi sin lógica | ~1.430 objetos por publicación; consultas nuevas requieren re-diseñar el layout | Mínimo: superficie de solo lectura sobre objetos estáticos |
| SQLite WASM (sql.js) leyendo el `.db` de R2 | SQL completo; cero cambios en el pipeline | Bundle WASM ~1 MB en el Worker; cargar y parsear 2 MB por isolate/cold start; presión de memoria/CPU en el edge | Motor SQL expuesto a entrada del usuario (amplía T10) |
| Réplica en Cloudflare D1 | SQLite nativo del edge, queries rápidas | Doble fuente de verdad (pipeline debe escribir también a D1), drift posible frente al artefacto, mayor atadura a Cloudflare vs. el multinube de ADR-0006 | Deriva silenciosa entre D1 y el `.db` publicado (nueva variante de T3) |

## Consecuencias

- Positivas: RF09–RF12 se resuelven con lecturas de objetos; RNF04 (p95 < 500 ms) es alcanzable trivialmente; RF17 sale de `indice.json`; la integridad hereda el mecanismo existente (sha256/etag del artefacto). RNF06 queda garantizado por construcción: la publicación JSON y el `.db` salen de la misma corrida.
- Negativas / deuda asumida: el layout de publicación es un contrato más a versionar (se documenta en `architecture.md` §Contratos y en el OpenAPI); una consulta futura fuera de las cuatro formas (p. ej. filtros arbitrarios) exigiría nueva ADR. Publicar ~1.430 objetos alarga la subida de rclone (aceptable: objetos pequeños, corrida diaria).
- Impacto en threat model: elimina el motor de consulta como superficie (reduce T10 a validación de parámetros y mapeo a claves de objeto); añade T14 (consistencia .db ↔ publicacion/) mitigada por la publicación conjunta y el `sha256` común en `indice.json`.
