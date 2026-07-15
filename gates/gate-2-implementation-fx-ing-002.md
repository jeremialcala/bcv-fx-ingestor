# Gate 2 — Implementation (FX-ING-002: consulta y descarga)

* **Estado:** draft
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 03-implementation
* **Versión:** 0.1.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | RF09–RF17 implementados según el diseño aprobado | Exportador: `aplicacion/exportar_publicacion.py` + `adaptadores/exportador_json.py` + `bcv-ingest exportar` (ADR-0007). Worker: `deploy/cloudflare/worker.js` (RF09–RF13, RF16, RF17) + `ui.js` (RF14, RF15) | ⬜ |
| 2 | RS06–RS11 implementados | RS06: guard default-deny con SHA-256 + `timingSafeEqual`; RS07: secret Wrangler, clave solo en header y en memoria en la UI; RS08: allowlist de parámetros + mapeo cerrado a objetos R2; RS09: `LIMITE_MAX` 1000 + regla de plataforma (runbook); RS10: `no-store`, CSP `default-src 'none'`, nosniff; RS11: log JSON por id de clave, jamás la clave | ⬜ |
| 3 | Contratos respetados | `openapi-consulta.yaml` verificado por la suite vitest; layout `publicacion/` (ultima/jornadas/series/monedas/indice) según architecture.md §Contrato de publicación; `/estado` y `/bcv_fx.db` con tests de regresión de shape exacto | ⬜ |
| 4 | Pirámide de tests en verde | 93 tests pytest (98.51% de cobertura, umbral 90%) + 43 tests vitest del contrato del Worker en workerd real (`@cloudflare/vitest-pool-workers`) | ⬜ |
| 5 | Métrica: paridad publicación ↔ base (PRD FX-ING-002) | Export real sobre el corpus completo: `indice.totales` = {jornadas 1393, tasas 30784} idéntico a `bcv-ingest estado`; sha256 del índice = hash real del `.db`; las 5 cuarentenas no aparecen en la publicación | ⬜ |
| 6 | Métrica: 100% de requests sin clave válida rechazados | Suite vitest: 401 en toda ruta `/api/*` (incluidas inexistentes) sin clave y con clave inválida; la clave por query string no autentica | ⬜ |
| 7 | Verificación E2E local | E2E de CLI: cargar fixture real → exportar → publicación verificada en disco (CHF del 31/03 fuera de `ultima.json`, serie CHF con 2 filas). Contrato del Worker ejercitado contra R2 de miniflare sembrado con la publicación | ⬜ |
| 8 | Hallazgos de implementación documentados | API del pool de vitest 4 (`cloudflareTest` como plugin, el export `./config` ya no existe); `allowScripts` de npm para workerd/esbuild registrado en `package.json`; CHF publicable en 2 de 3 jornadas (paridad exacta, no exclusión por moneda) | ⬜ |
| 9 | CHANGELOG al día | `[Unreleased]` con la fase 03 del feature completa | ⬜ |
| 10 | **Aprobación humana del gate** | — | ⬜ pendiente |

Nota de secuencia: la imagen `v1.2.0` que referencia el CronJob no incluye `exportar`; los
manifests quedan listos y se activan con la imagen que publique el corte de este gate. La
verificación E2E de esta fase se hizo con el paquete local + miniflare, no contra el clúster.

Abierto trasladado desde el Gate 1: umbral del rate limiting de plataforma — documentado en
el runbook (§Despliegue inicial), se configura y verifica al desplegar.

Abierto: procedimiento de claves API documentado en el runbook (RS07); la entrega/rotación
real ocurre al desplegar.

Heredado del charter: confirmar stakeholders operador/analista (`<TODO>`).
