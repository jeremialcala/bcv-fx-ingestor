# Gate 5 — Monitoring

* **Estado:** review
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 06-monitoring
* **Versión:** 1.0.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | SLIs/SLOs definidos y dimensionados al sistema | `observability.md` §SLIs y SLOs (6 SLOs; frescura con doble medición edge/origen) | ✅ |
| 2 | SLOs monitorizados con alerta | `health.yml` (frescura, mar–sáb, email al fallar), `smoke.yml` (drift, lunes), re-scan semanal en `ci.yml` (CVEs, A09), `activeDeadlineSeconds` (duración) | ✅ |
| 3 | Instrumentación real probada | bloque `frescura` en `bcv-ingest estado` (79 tests en verde; verificado contra el corpus real: última jornada 2026-07-10, 2 días); corrida verde de `health.yml` con el guard de `WORKER_URL` | ⬜ falta la corrida de health |
| 4 | Proceso de incidentes documentado | `observability.md` §stateDiagram del incidente + §matriz señal→diagnóstico→acción; regla de postmortem → CHANGELOG/ADR/threat model | ✅ |
| 5 | Proceso de incidentes ejercitado (no aspiracional) | Dos incidentes reales resueltos con postmortem trazado: cadena TLS incompleta (ADR-0004 §Nota, intermedio vendorizado) y falsos positivos ANG/BOB (RF04 recalibrado, tests de regresión) | ✅ |
| 6 | Evidencia en 3 ejes | `observability.md`: C4Deployment de telemetría · sequence señal→alerta→operador · stateDiagram incidente · timeline de hitos (4/4 Mermaid válidos) | ✅ |
| 7 | Monitoreo de seguridad (A09) | §Monitoreo de seguridad: auditoría de cuarentenas (RS04), integridad por hash, gitleaks por push, SCA/container semanal | ✅ |
| 8 | On-call definido | Operador de datos (rol del charter) — nombre pendiente del `<TODO>` de stakeholders | ✅ rol / ⬜ nombre |
| 9 | CHANGELOG al día | `[Unreleased]` con la fase 06 completa | ✅ |
| 10 | **Aprobación humana del gate** | — | ⬜ pendiente (HITL) |

Abierto trasladado desde el Gate 0: confirmar stakeholders operador/analista (charter) — con
el Gate 5 el rol de on-call lo hace operativamente relevante.

Al aprobar: cortar `[Unreleased]` → **`1.0.0`** (primer release productivo, cierre del ciclo
AI-DLC), sincronizar `pyproject.version`, tag `v1.0.0` (publica imagen GHCR `v1.0.0` +
`latest`) y actualizar el tag de imagen del CronJob en `deploy/k8s/base/cronjob.yaml`.
