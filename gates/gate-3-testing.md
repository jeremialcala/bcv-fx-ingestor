# Gate 3 — Testing

* **Estado:** approved
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 04-testing
* **Versión:** 0.4.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | Estrategia de pruebas documentada (pirámide + fronteras real/mock) | `docs/04-testing/test-strategy.md` §Pirámide, C4 anotado por frontera | ✅ |
| 2 | Círculo requisito ↔ test cerrado (`verifies`) | `test-strategy.md` §requirementDiagram + tabla RF/RNF/RS completa | ✅ |
| 3 | Matriz de transición de estados cubierta | `test-strategy.md` §State-transition: 10/10 transiciones del ciclo Ingesta con test (se añadieron Cargado limpio, Fallido con rollback, reproceso de Cuarentena) | ✅ |
| 4 | Escenarios de abuso A1–A6 con test | `test-strategy.md` §Abuso ↔ test (incluye A4 re-ingesta alterada y 16 negativos del contrato de anclas — T1, la amenaza mejor puntuada del DREAD, probada rompiendo cada ancla una a una) | ✅ |
| 5 | Tests pasando | 78 tests (43 unit, 31 integración, 4 e2e), cobertura 99% — las 4 líneas restantes justificadas en `test-strategy.md` §Líneas aceptadas | ✅ |
| 6 | DAST | No aplica, justificado: sin superficie de red entrante; equivalente dinámico = entrada hostil real + TLS verificado en vivo contra el portal (ADR-0004) | ✅ N/A |
| 7 | Rendimiento dentro de SLOs | RNF01: archivo trimestral real en 0.04 s < 30 s (medición + test de regresión `test_rendimiento.py`) | ✅ |
| 8 | Validación operativa sobre datos reales | Corpus completo 2020-TI→2026-TIII: 1.393 jornadas, 30.784 tasas, 5 anomalías reales aisladas; re-ingesta = 0 filas nuevas | ✅ |
| 9 | Diagramas válidos y CHANGELOG al día | 18/18 bloques Mermaid válidos; `[Unreleased]` con la fase 04 | ✅ |
| 10 | **Aprobación humana del gate** | — | ✅ aprobado 2026-07-12 (Jeremi Alcalá) |

Abierto trasladado desde el Gate 0: confirmar stakeholders operador/analista (charter).

Gate aprobado el 2026-07-12: `[Unreleased]` cortado a `0.4.0` en el CHANGELOG y
`test-strategy.md` en `approved`. Siguiente fase: 05-deployment (Gate 4 — pipeline CI
con gates de seguridad, runbook de operación).
