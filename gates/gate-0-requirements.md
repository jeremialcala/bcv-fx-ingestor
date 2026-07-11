# Gate 0 — Requirements

* **Estado:** review
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 01-requirements
* **Versión:** 0.1.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | Requisitos funcionales y no funcionales definidos | PRD §RF01–RF08, §RNF01–RNF03 | ✅ |
| 2 | Requisitos de seguridad mapeados a ASVS | PRD §Requisitos de seguridad (RS01–RS05, ASVS L1) | ✅ |
| 3 | Escenarios de abuso documentados | PRD §A1–A6 (incluye caso real CHF) | ✅ |
| 4 | Threat assessment inicial (DFD + DREAD) | PRD §Threat assessment (flowchart + quadrantChart) | ✅ |
| 5 | Clasificación de datos | `docs/00-project/data-classification.md` | ✅ |
| 6 | Charter y glosario (lenguaje ubicuo) | `charter.md` (mindmap), `glossary.md` | ✅ |
| 7 | Journey y trazabilidad de requisitos | PRD §journey, §requirementDiagram | ✅ |
| 8 | **Aprobación humana del gate** | — | ⬜ pendiente (HITL) |

Abiertos antes de aprobar: patrón de URLs de descarga del BCV (<TODO> en PRD); confirmar stakeholders operador/analista (charter).

Al aprobar: cortar `[Unreleased]` → `0.1.0` en CHANGELOG (ya preparado) y pasar artefactos de fase 00/01 a `approved`.
