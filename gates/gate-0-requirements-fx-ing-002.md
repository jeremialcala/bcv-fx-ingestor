# Gate 0 — Requirements (FX-ING-002: consulta y descarga)

* **Estado:** approved
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 01-requirements
* **Versión:** 0.2.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | Requisitos funcionales y no funcionales definidos | PRD FX-ING-002 §RF09–RF17, §RNF04–RNF07 | ✅ |
| 2 | Requisitos de seguridad mapeados a ASVS | PRD §Requisitos de seguridad (RS06–RS11, ASVS L1) | ✅ |
| 3 | Escenarios de abuso documentados | PRD §A1–A6 | ✅ |
| 4 | Threat assessment inicial (DFD + DREAD) | PRD §Threat assessment (flowchart + quadrantChart, T1–T7) | ✅ |
| 5 | Clasificación de datos | `docs/00-project/data-classification.md` v0.3.0 (clave API como secreto operativo) | ✅ |
| 6 | Charter y glosario (lenguaje ubicuo) | `charter.md` v0.3.0 (§Alcance + mindmap + R5), `glossary.md` v0.3.0 (contexto Consulta Cambiaria) | ✅ |
| 7 | Journey y trazabilidad de requisitos | PRD §journey, §requirementDiagram | ✅ |
| 8 | **Aprobación humana del gate** | — | ✅ aprobado 2026-07-14 (Jeremi Alcalá) |

Abierto trasladado a 02-design (Gate 1): mecanismo de consulta en el edge — SQLite WASM sobre R2 vs. réplica D1 vs. JSON precalculado — a decidir en ADR-0007, que supersede parcialmente ADR-0006 ("solo distribución").

Abierto trasladado a 02-design (Gate 1): mecanismo de rate limiting (WAF de Cloudflare vs. lógica en el Worker) según el plan contratado.

Abierto: procedimiento de alta/rotación/revocación de claves API (manual, a cargo del owner; RS07).

Heredado del charter: confirmar stakeholders operador/analista (`<TODO>`), ahora también usuarios directos del servicio de consulta.

Gate aprobado el 2026-07-14: el PRD FX-ING-002 pasa a `approved` y la versión `1.1.0` queda cortada en el CHANGELOG. A partir de este gate el repositorio adopta gitflow (develop/feature/release) para el trabajo del feature.
