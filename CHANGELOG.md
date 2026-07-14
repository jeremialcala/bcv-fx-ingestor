# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [1.1.0] - 2026-07-14

### Añadido

- Overlay `deploy/k8s/overlays/local` para despliegue local (kind/docker-desktop): mismo CronJob real con publicación a `/data/publicado` en vez de nubes; añadido al gate de IaC del CI y al runbook (§Despliegue local). Verificado end-to-end en el equipo del operador: ingesta real de 2026-TIII dentro del clúster (8 jornadas, 168 tasas, TLS estricto con el intermedio vendorizado), artefacto extraído del PVC y servido por el Worker en miniflare con integridad SHA-256 confirmada.
- Fase 01-requirements del feature FX-ING-002 (rumbo al Gate 0): PRD `docs/01-requirements/consulta-descarga-fx.md` — API JSON de consulta y Web UI de consulta/descarga sobre el Worker de Cloudflare existente, protegidas por clave API (RF09–RF17, RNF04–RNF07, escenarios de abuso A1–A6, DFD + quadrant DREAD T1–T7); checklist `gates/gate-0-requirements-fx-ing-002.md` (draft, aprobación humana pendiente).

### Cambiado

- Gate 0 del feature FX-ING-002 aprobado el 2026-07-14 (Jeremi Alcalá); el PRD `consulta-descarga-fx.md` pasa a `approved` y este corte publica la imagen `v1.1.0` (el CronJob de K8s la referencia). El repositorio adopta **gitflow** (develop/feature/release) para el trabajo del feature, en reemplazo del trunk-based del ciclo 0.x–1.0.
- Levantado parcialmente el no-scope de API de consulta y UI (decisión 2026-07-14): charter §Alcance, mindmap y riesgos (0.2.0 → 0.3.0) y PRD FX-ING-001 §Objetivos (0.3.0 → 0.4.0) anotados sin reescribir historia; la consulta REST/JSON y la Web UI pasan al alcance vía FX-ING-002. GraphQL, dashboards analíticos, escritura de datos y tasas derivadas siguen fuera. Glosario con el contexto acotado Consulta Cambiaria (Clave API, Consulta puntual, Serie; 0.2.0 → 0.3.0). ADR-0007 (mecanismo de consulta en el edge, supersede parcialmente ADR-0006) queda pendiente para el Gate 1.

### Seguridad

- Definidos RS06–RS11 (ASVS L1) para la nueva superficie de consulta: default-deny con clave API, secreto en Wrangler, validación allowlist de parámetros, anti-automatización (rate limiting y topes de página), control de caché/headers y auditoría de uso por clave. La clave API queda clasificada como secreto operativo Confidencial en `data-classification.md` (0.2.0 → 0.3.0).

## [1.0.0] - 2026-07-12

Primer release productivo: cierra el ciclo AI-DLC completo (gates 0–5 aprobados).

### Añadido

- Fase 06-monitoring (Gate 5): `docs/06-monitoring/observability.md` con 6 SLOs dimensionados al sistema (frescura del artefacto con doble medición edge/origen, drift de la fuente, éxito de ingesta, cuarentenas, pipeline, duración), C4Deployment de telemetría, sequence señal→alerta→operador, stateDiagram del ciclo de incidente con matriz señal→diagnóstico→acción, y timeline de hitos; checklist `gates/gate-5-monitoring.md`.
- Instrumentación de monitoreo: bloque `frescura` en `bcv-ingest estado` (última fecha de operación, edad en días, última ingesta — SLI primario, con test de integración; 79 tests) y workflow `health.yml` (mar–sáb) que vigila la edad del artefacto publicado vía el `/estado` del Worker, con guard que lo deja listo-pero-inactivo hasta configurar `WORKER_URL`.
- Badge de salud del artefacto en el README.

### Cambiado

- Gate 5 (monitoring) aprobado el 2026-07-12 (Jeremi Alcalá); `observability.md` pasa a `approved`, el CronJob de K8s apunta a la imagen `v1.0.0` y el proyecto entra en operación. Abierto trasladado: stakeholders operador/analista en el charter (ahora relevante como on-call).

### Seguridad

- Re-scan semanal programado en `ci.yml` (lunes): SAST, SCA y escaneo de imagen re-corren aunque no haya cambios de código — las CVEs nuevas no esperan commits (A09).

## [0.5.0] - 2026-07-12

### Añadido

- Fase 05-deployment (Gate 4): pipeline CI en GitHub Actions con los gates de seguridad de la metodología — tests (matriz 3.11/3.12, cobertura ≥ 90%), SAST (bandit), SCA (pip-audit), secrets (gitleaks), license (allowlist), docs (Mermaid), container (build + Trivy, push a GHCR en tags con verificación tag == versión) e IaC (kubeconform + Trivy config); smoke semanal no bloqueante contra el portal real (`smoke.yml`). Badges de CI, smoke y última versión en el README.
- Despliegue multinube edge-first: `Dockerfile` multi-stage no-root, manifests K8s con kustomize (base + overlays EKS/GKE) — CronJob de días hábiles con ingesta fail-closed y publicación del artefacto a S3/GCS/R2 vía rclone — y Worker de Cloudflare que sirve `bcv_fx.db` desde R2 (`/bcv_fx.db`, `/estado`), sin API de consulta (no-scope del PRD).
- `docs/05-deployment/deployment.md` (C4Deployment, flowchart del pipeline con rollback, gantt de cutover, runbook), ADR-0005 (CI GitHub Actions), ADR-0006 (multinube edge-first) y checklist `gates/gate-4-deployment.md`.
- Scripts vendorizados al repo para CI y documentación viva: `scripts/validate_mermaid.py` (fix npm en Windows, caché configurable) y `scripts/gitgraph_from_log.py` (fix de encoding UTF-8).

### Cambiado

- Gate 4 (deployment) aprobado el 2026-07-12 (Jeremi Alcalá); `deployment.md` pasa a `approved` y el tag `v0.5.0` publica la primera imagen oficial a GHCR. Abierto trasladado: stakeholders operador/analista en el charter.

### Corregido

- `pyproject.version` desincronizado (0.3.0 → 0.4.0, y 0.5.0 con este corte); en adelante el job `container` del CI verifica que cada tag `vX.Y.Z` coincida con la versión del paquete.
- Smoke: el runner de Ubuntu necesita el intermedio de Sectigo instalado (mismo hallazgo TLS que el contenedor); la primera corrida roja fue el fallo cerrado actuando según diseño.

### Seguridad

- Hallazgo del contenedor Linux: OpenSSL no resuelve vía AIA la cadena TLS incompleta del BCV (a diferencia del verificador de Windows), así que la imagen vendoriza el certificado intermedio público de Sectigo (`deploy/docker/ca-extra/`, huella SHA-256 documentada) — la política de fallo cerrado de ADR-0004 queda intacta. Imagen escaneada con Trivy: 0 vulnerabilidades HIGH/CRITICAL con fix (pip de la base actualizado).

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

[Unreleased]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.5.0...v1.0.0
[0.5.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jeremialcala/bcv-fx-ingestor/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jeremialcala/bcv-fx-ingestor/releases/tag/v0.1.0
