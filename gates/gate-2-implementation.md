# Gate 2 — Implementation

* **Estado:** approved
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 03-implementation
* **Versión:** 0.3.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | RF01–RF08 implementados según el diseño aprobado | `src/bcv_ingest/` (hexagonal: dominio/aplicacion/adaptadores, puertos del classDiagram) | ✅ |
| 2 | RS01–RS05 implementados | RS01: `descargador_http.py` (TLS estricto vía truststore, ADR-0004); RS02: límites en `lector_xls.py`; RS03: queries parametrizadas; RS04: SHA-256 + logs de cuarentena; RS05: constraints UNIQUE/CHECK/FK | ✅ |
| 3 | Contrato de CLI y schema respetados | `cli.py` (exit codes 0/2/3, JSON), `repositorio_sqlite.py` (DDL de architecture.md §Contratos) | ✅ |
| 4 | Pirámide de tests en verde | 42 tests: 25 unit (dominio) + 14 integración (xlrd/SQLite/httpx-mock) + 3 e2e (CLI real) | ✅ |
| 5 | Métrica: anomalía CHF 31/03/2020 detectada automáticamente | e2e `test_cargar_estado_y_reingesta`; verificación real contra el portal (2026-07-12) | ✅ |
| 6 | Métrica: re-ingesta produce 0 filas nuevas | `test_guardar_jornada_es_idempotente_rf05`, e2e E3 (estado `duplicado`, exit 0) | ✅ |
| 7 | Verificación E2E real contra el portal BCV | descarga 2020-TI (sha256 `c62e6e…`), 404 limpio en 2019-TIV, `omitido_ya_ingerido` en re-descarga (RF01) | ✅ |
| 8 | Hallazgos de implementación documentados | RF04 refinado (spread entre bases) en PRD; cadena TLS incompleta del BCV en ADR-0004 y threat model | ✅ |
| 9 | CHANGELOG al día | `[Unreleased]` con la fase 03 completa | ✅ |
| 10 | **Aprobación humana del gate** | — | ✅ aprobado 2026-07-12 (Jeremi Alcalá) |

Abierto trasladado desde el Gate 0: confirmar stakeholders operador/analista (charter).

Gate aprobado el 2026-07-12: `[Unreleased]` cortado a `0.3.0` en el CHANGELOG. El proyecto pasa a fase de operación (ingesta del corpus completo 2020-TI → presente).
