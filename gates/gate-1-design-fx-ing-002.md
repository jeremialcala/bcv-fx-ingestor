# Gate 1 — Design (FX-ING-002: consulta y descarga)

* **Estado:** approved
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 0.2.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | Arquitectura C4 validada para el feature | PRD FX-ING-002 §C4Context; `architecture.md` §Distribución y consulta (C4Container edge) | ✅ |
| 2 | Threat model STRIDE extendido a la superficie nueva | `threat-model.md` §DFD del edge + filas STRIDE (Guard, API, Cache, Publicación R2, Web UI) | ✅ |
| 3 | Amenazas priorizadas con DREAD y control por amenaza | `threat-model.md` §DREAD (T9–T15, score + control; ≥6.0 todas con dueño) | ✅ |
| 4 | ADRs de decisiones estructurales | ADR-0007 (JSON precalculado en R2, supersede parcialmente ADR-0006) · ADR-0008 (rate limiting en plataforma) | ✅ |
| 5 | Contratos definidos | `contracts/openapi-consulta.yaml` (API + auth + errores) · `architecture.md` §Contrato de publicación (`publicacion/`) · CLI `exportar` | ✅ |
| 6 | Flujo crítico del feature | `architecture.md` §Flujo crítico de consulta (sequenceDiagram con auth, validación y 404 controlado) | ✅ |
| 7 | Modelo de dominio del bounded context nuevo | `architecture.md` §Contextos acotados (Consulta Cambiaria); publicación derivada — sin entidades nuevas en SQLite | ✅ |
| 8 | Patrones de seguridad por amenaza priorizada | `architecture.md` §Patrones de seguridad (T9–T15 → RS06–RS11, ADR-0007/0008) | ✅ |
| 9 | **Decisiones HITL: mecanismo de consulta y rate limiting** | Decididas 2026-07-14 (Jeremi Alcalá): JSON precalculado (ADR-0007) y plataforma + topes (ADR-0008) | ✅ decididas 2026-07-14 |
| 10 | **Aprobación humana del gate** | — | ✅ aprobado 2026-07-14 (Jeremi Alcalá) |

Abierto trasladado a 03-implementation: umbral y ventana del rate limiting de plataforma (configuración fuera del repo) — documentar y verificar en el runbook de `deployment.md` (deuda de ADR-0008).

Abierto trasladado a 03-implementation: harness de tests JS del Worker (vitest + miniflare) — el Worker no tiene hoy `package.json` ni tests (dependencia anotada en el PRD §Dependencias).

Abierto: procedimiento operativo de alta/rotación/revocación de claves API (RS07) — redactar con el runbook en la fase de despliegue.

Heredado del charter: confirmar stakeholders operador/analista (`<TODO>`).

Gate aprobado el 2026-07-14: `architecture.md`, `threat-model.md` y el contrato OpenAPI pasan a `approved`; versión `1.2.0` cortada en el CHANGELOG. Siguiente paso: fase 03-implementation del feature (exportador de publicación, Worker con guard + API + UI, harness vitest/miniflare) rumbo al Gate 2.
