# Gate 1 — Design

* **Estado:** review
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 0.1.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | Arquitectura C4 validada (Context/Container/Component) | PRD §C4Context; `architecture.md` §C4 Container/Component | ✅ diagramas listos, validación humana ⬜ |
| 2 | Threat model STRIDE completo | `threat-model.md` §STRIDE (6 componentes) | ✅ |
| 3 | Amenazas priorizadas con DREAD y control por amenaza | `threat-model.md` §DREAD (T1–T8, score + control) | ✅ |
| 4 | ADRs de decisiones estructurales | ADR-0001, ADR-0002, ADR-0003 | ✅ |
| 5 | Contratos definidos | `architecture.md` §Contratos (CLI + DDL SQLite) — no hay API de red | ✅ |
| 6 | Flujo crítico y ciclo de vida de entidad núcleo | `architecture.md` §sequence, §stateDiagram (Ingesta) | ✅ |
| 7 | Modelo de datos y dominio | `architecture.md` §erDiagram, §classDiagram | ✅ |
| 8 | Patrones de seguridad por amenaza priorizada | `architecture.md` §Patrones de seguridad | ✅ |
| 9 | **Decisión HITL: política TLS ante certificado inválido del BCV** | `threat-model.md` §Controles | ⬜ pendiente |
| 10 | **Aprobación humana del gate** | — | ⬜ pendiente (HITL) |

Al aprobar: cortar `[Unreleased]` → `0.2.0` en CHANGELOG, pasar artefactos 02-design a `approved`, y arrancar 03-implementation (esqueleto `src/` + pirámide `tests/`).
