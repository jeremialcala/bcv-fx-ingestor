# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.4.0] - 2026-07-12

### Añadido

- Fase 04-testing (Gate 3): estrategia de pruebas `docs/04-testing/test-strategy.md` con C4 anotado por frontera (real vs. mock), state-transition testing del ciclo Ingesta (10/10 transiciones con test) y `requirementDiagram` con `verifies` que cierra el círculo requisito↔test del Gate 0; checklist `gates/gate-3-testing.md`.
- Tests de las transiciones que faltaban (Cargado limpio, Fallido con rollback A1, reproceso de Cuarentena sin acumulación, re-ingesta alterada A4), límites RS02 de hojas/filas, auditoría de logs RS04 y rendimiento RNF01 (archivo trimestral real en 0.04 s < 30 s).
- Cierre de brechas de la evaluación del Gate 3: 16 negativos del contrato de anclas con hojas falsas duck-typed (T1: cada ancla del layout rota una a una, libro sin hojas, hoja corrupta sin abortar el lote), contrato del comando `descargar` con descargador simulado (incluida la ruta `ErrorDescarga` → exit 3) y estado `cuarentena` con parseo exitoso pero nada cargable. La suite pasa a 78 tests con 99% de cobertura; las 4 líneas restantes quedan justificadas en `test-strategy.md`.

### Cambiado

- Gate 3 (testing) aprobado el 2026-07-12 (Jeremi Alcalá); `test-strategy.md` pasa a `approved`. Abierto trasladado: stakeholders operador/analista en el charter.

- Documentación viva de la fase 03 exigida por la metodología: `docs/03-implementation/repo-history.md` con gitGraph derivado del historial real, bitácora de commits y trazabilidad tag ↔ versión ↔ ADR (auditoría AI-DLC 2026-07-12).
- Tests en proceso de la CLI y del caso de uso DescargarPeriodo; la suite pasa a 51 tests con cobertura medida del 92% (umbral del catálogo: 80%), incluidos los casos reales ANG y BOB como regresión de la calibración de RF04.
- Validación operativa del corpus completo 2020-TI → 2026-TIII desde el portal BCV (27 archivos): 1.393 jornadas, 30.784 tasas y 5 cuarentenas — todas anomalías genuinas de la fuente: CHF 31/03/2020 (divergencia 10.32x), BRL 20/07/2020, TRY 21/04/2021 y ARS 05/04/2022 (BID>ASK por dígitos corridos) y ANG 17/11/2021 (valor ausente). La re-ingesta de los 27 archivos produce 0 filas nuevas (métrica del PRD cumplida sobre el corpus real).

### Corregido

- Auditoría AI-DLC: cabeceras de metadatos sincronizadas con los cortes de versión de los gates (artefactos de fases 00–02 a `0.2.0`/`0.3.0` según su última modificación; ADR-0002 y ADR-0004 a `1.1.0`).
- Regla de coherencia de spread de RF04 recalibrada contra el corpus completo (2026-07-12): divergencia multiplicativa entre bases con umbral 1.25 en lugar de diferencia absoluta 0.05. La primera ingesta del corpus produjo 517 falsos positivos (ANG en banda oficial ~5,3% desde 2023, BOB ~5,6% en 2024-2025) que la regla recalibrada elimina conservando la detección de errores reales (divergencia mínima observada en error genuino: 10.32x).
- Hallazgos SAST de bandit en `repositorio_sqlite.py` (B608 consulta construida con f-string y B101 assert): los conteos usan ahora un mapa de SQL literal.

### Seguridad

- Verificación transversal del Gate 2 según el catálogo AI-DLC: bandit 0 hallazgos, pip-audit sin vulnerabilidades en dependencias de runtime (pip del venv actualizado a 26.1.2) y 15/15 diagramas Mermaid válidos. Anexo de evidencia en `gates/gate-2-implementation.md`.

## [0.3.0] - 2026-07-12

### Añadido

- Implementación completa de la fase 03 (`src/bcv_ingest/`, arquitectura hexagonal del diseño aprobado): dominio puro (modelos, catálogo de 23 monedas, tabla de redenominaciones, validador), casos de uso (ingestar, descargar por período, consultar estado), adaptadores (lector xlrd con contrato de anclas, repositorio SQLite con el DDL del contrato, descargador HTTPS estricto, carpeta local) y CLI `bcv-ingest` (descargar/cargar/estado, exit codes 0/2/3, salida JSON).
- Pirámide de tests (42): 25 unitarios de dominio, 14 de integración (xlrd contra el archivo real, SQLite, httpx simulado) y 3 e2e de la CLI; fixture oficial `tests/fixtures/2_1_2a20_smc.xls` (sha256 `c62e6e43…`).
- Checklist `gates/gate-2-implementation.md`.

### Cambiado

- RF04 refinado con evidencia real: la anomalía CHF 31/03/2020 cumple BID≤ASK numéricamente; se añadió la regla de coherencia de spread entre las bases M.E./US$ y Bs./M.E., que es la que la detecta (PRD §Requisitos funcionales).
- Gate 2 (implementation) aprobado el 2026-07-12 (Jeremi Alcalá); el proyecto pasa a fase de operación. Abierto trasladado: stakeholders operador/analista en el charter.

### Seguridad

- Verificación E2E real contra el portal: la política de fallo cerrado (ADR-0004) se disparó porque el BCV envía una cadena TLS incompleta; el descargador valida contra el almacén de confianza del SO vía `truststore` (verificación estricta, sin vía de excepción). Documentado en ADR-0004 §Nota de implementación y threat model.

## [0.2.0] - 2026-07-11

### Añadido

- Diseño del sistema (`docs/02-design/architecture.md`): C4 Container/Component, secuencia del flujo de ingesta, ciclo de vida de la entidad Ingesta, ER y modelo de dominio hexagonal, contrato de CLI y schema SQLite.
- Threat model STRIDE + DREAD (`docs/02-design/threat-model.md`) con DFD y quadrant de priorización.
- ADR-0001 (SQLite como almacén), ADR-0002 (ingesta dual descarga + local), ADR-0003 (parser xlrd con validación de dominio), ADR-0004 (TLS estricto sin mecanismo de excepción).
- Checklist `gates/gate-1-design.md`.

### Cambiado

- Patrón de URLs de descarga del BCV confirmado contra el portal (2026-07-11) y documentado en PRD, ADR-0002 y glosario: `2_1_2{t}{AA}_smc.xls` por trimestre (`a`–`d` = I–IV), histórico desde 2020-TI, 404 en períodos inexistentes. Resuelve el abierto correspondiente del Gate 0.
- Threat model: evidencia registrada de que el certificado TLS actual del portal valida correctamente.
- Gates 0 (requirements) y 1 (design) aprobados el 2026-07-11 (Jeremi Alcalá); artefactos de las fases 00–02 pasan a `approved`. Abierto trasladado: stakeholders operador/analista en el charter.

### Seguridad

- Decisión HITL (2026-07-11): política TLS de fallo cerrado — ante certificado inválido del portal BCV el proceso falla siempre, sin flag `--inseguro` ni vía de excepción; respaldo operativo por modo local. Documentada en ADR-0004 y propagada a threat model (T2), arquitectura (§Patrones de seguridad) y PRD (RS01). Cierra el criterio 9 del Gate 1.

## [0.1.0] - 2026-07-11

### Añadido

- Charter del proyecto con mindmap de alcance (`docs/00-project/charter.md`).
- Glosario / lenguaje ubicuo del dominio cambiario BCV (`docs/00-project/glossary.md`).
- Clasificación de datos (`docs/00-project/data-classification.md`).
- PRD `docs/01-requirements/ingesta-historicos-fx.md` con escenarios de abuso, C4 Context, journey, trazabilidad ASVS y threat assessment inicial (DFD + quadrant DREAD).
- Checklist `gates/gate-0-requirements.md`.

### Seguridad

- Anomalía real detectada en el modelo fuente (CHF 31/03/2020: BID 0.96273 vs ASK 9.96296) documentada como evidencia del requisito de validación BID≤ASK.

[Unreleased]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeremialcala/bcv-fx-ingestor/releases/tag/v0.1.0
