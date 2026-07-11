# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

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

[Unreleased]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeremialcala/bcv-fx-ingestor/releases/tag/v0.1.0
