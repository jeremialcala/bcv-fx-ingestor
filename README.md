# bcv-fx-ingestor

[![CI](https://github.com/jeremialcala/bcv-fx-ingestor/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jeremialcala/bcv-fx-ingestor/actions/workflows/ci.yml)
[![Smoke ingesta real](https://github.com/jeremialcala/bcv-fx-ingestor/actions/workflows/smoke.yml/badge.svg)](https://github.com/jeremialcala/bcv-fx-ingestor/actions/workflows/smoke.yml)
[![Salud del artefacto](https://github.com/jeremialcala/bcv-fx-ingestor/actions/workflows/health.yml/badge.svg)](https://github.com/jeremialcala/bcv-fx-ingestor/actions/workflows/health.yml)
[![Última versión](https://img.shields.io/github/v/tag/jeremialcala/bcv-fx-ingestor?label=versi%C3%B3n&sort=semver)](https://github.com/jeremialcala/bcv-fx-ingestor/tags)

Proceso de ingesta y carga de los tipos de cambio de referencia históricos del Banco Central de Venezuela (BCV) hacia SQLite, con CLI en Python.

Proyecto estructurado con la metodología **AI-DLC** (seguridad por diseño, gates con Human-in-the-Loop).

## Estado

| Fase | Gate | Estado |
|---|---|---|
| 00-project | — | approved |
| 01-requirements | Gate 0 | ✅ aprobado 2026-07-11 |
| 02-design | Gate 1 | ✅ aprobado 2026-07-11 |
| 03-implementation | Gate 2 | ✅ aprobado 2026-07-12 |
| 04-testing | Gate 3 | ✅ aprobado 2026-07-12 |
| 05-deployment | Gate 4 | ✅ aprobado 2026-07-12 |
| 06-monitoring | Gate 5 | ✅ aprobado 2026-07-12 — ciclo AI-DLC completo (v1.0.0) |

## Uso

```bash
# instalar (Python 3.11+)
pip install -e .

# descargar del portal BCV e ingerir (TLS estricto, sin re-descargar lo ya ingerido)
bcv-ingest descargar --desde 2020-01 --hasta 2020-12

# ingerir archivos colocados manualmente (archivo o carpeta)
bcv-ingest cargar entrada/

# estado de ingestas y cuarentenas pendientes
bcv-ingest estado
bcv-ingest estado --jornada 2020-03-31
```

Exit codes: `0` OK, `2` hubo cuarentenas, `3` error de red o TLS. La salida de datos
es JSON por stdout; los logs de auditoría van por stderr. La base por defecto es
`bcv_fx.db` (opción `--db`).

## Despliegue

Multinube edge-first (detalle y runbook en `docs/05-deployment/deployment.md`, ADR-0005/0006):

- **Contenedor**: `docker build -t bcv-fx-ingestor .` — imagen no-root con TLS estricto;
  en tags `vX.Y.Z` el CI la publica en `ghcr.io/jeremialcala/bcv-fx-ingestor`.
- **K8s (AWS o GCP)**: `kubectl apply -k deploy/k8s/overlays/eks` (o `gke`) — CronJob de
  días hábiles que ingiere el trimestre en curso y publica `bcv_fx.db` a S3/GCS/R2 con rclone.
- **Edge (Cloudflare)**: `cd deploy/cloudflare && npx wrangler deploy` — Worker que sirve
  el artefacto desde R2 (`GET /bcv_fx.db`, `GET /estado`). Sin API de consulta (no-scope).

## Estructura

```
bcv-fx-ingestor/
├── CHANGELOG.md
├── pyproject.toml
├── docs/
│   ├── 00-project/
│   │   ├── charter.md
│   │   ├── glossary.md
│   │   ├── data-classification.md
│   │   └── adr/
│   │       ├── 0001-sqlite-como-almacen.md
│   │       ├── 0002-ingesta-dual-descarga-y-local.md
│   │       ├── 0003-parser-xlrd-con-validacion-de-dominio.md
│   │       └── 0004-tls-estricto-sin-excepciones.md
│   ├── 01-requirements/
│   │   └── ingesta-historicos-fx.md        # PRD (Gate 0)
│   ├── 02-design/
│   │   ├── architecture.md                 # Gate 1
│   │   └── threat-model.md                 # Gate 1
│   ├── 03-implementation/
│   │   └── repo-history.md                 # Gate 2 (documentación viva: gitGraph + bitácora)
│   ├── 04-testing/
│   │   └── test-strategy.md                # Gate 3 (pirámide, transiciones, requisito↔test)
│   ├── 05-deployment/
│   │   └── deployment.md                   # Gate 4 (C4Deployment, pipeline, runbook)
│   └── 06-monitoring/
│       └── observability.md                # Gate 5 (SLOs, incidentes, telemetría)
├── src/bcv_ingest/
│   ├── dominio/                            # entidades, validador, puertos (Python puro)
│   ├── aplicacion/                         # casos de uso
│   ├── adaptadores/                        # xlrd, sqlite3, httpx, carpeta local
│   └── cli.py                              # bcv-ingest (contrato público)
├── tests/
│   ├── unit/ · integration/ · e2e/
│   └── fixtures/2_1_2a20_smc.xls           # archivo oficial real (2020-TI, caso CHF)
├── deploy/
│   ├── docker/ca-extra/                    # intermedio Sectigo (cadena incompleta del BCV)
│   ├── k8s/                                # base + overlays eks/gke (kustomize)
│   └── cloudflare/                         # Worker + wrangler.toml (distribución edge)
├── .github/workflows/                      # ci.yml (gates + re-scan) · smoke.yml · health.yml
├── Dockerfile
├── scripts/                                # validate_mermaid.py · gitgraph_from_log.py
└── gates/
    ├── gate-0-requirements.md
    ├── gate-1-design.md
    ├── gate-2-implementation.md
    ├── gate-3-testing.md
    ├── gate-4-deployment.md
    └── gate-5-monitoring.md
```

## Modelo de datos fuente

Archivos oficiales `2_1_2*_smc.xls` del BCV: una hoja por fecha de operación (`DDMMYYYY`), ~23 monedas por hoja, cotizaciones BID/ASK en M.E./US$ y en Bs./M.E., con fecha de operación y fecha valor. Ver `docs/00-project/glossary.md`.
