# bcv-fx-ingestor

Proceso de ingesta y carga de los tipos de cambio de referencia históricos del Banco Central de Venezuela (BCV) hacia SQLite, con CLI en Python.

Proyecto estructurado con la metodología **AI-DLC** (seguridad por diseño, gates con Human-in-the-Loop).

## Estado

| Fase | Gate | Estado |
|---|---|---|
| 00-project | — | approved |
| 01-requirements | Gate 0 | ✅ aprobado 2026-07-11 |
| 02-design | Gate 1 | ✅ aprobado 2026-07-11 |
| 03-implementation | Gate 2 | evidencia completa, pendiente aprobación humana |

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
│   └── 02-design/
│       ├── architecture.md                 # Gate 1
│       └── threat-model.md                 # Gate 1
├── src/bcv_ingest/
│   ├── dominio/                            # entidades, validador, puertos (Python puro)
│   ├── aplicacion/                         # casos de uso
│   ├── adaptadores/                        # xlrd, sqlite3, httpx, carpeta local
│   └── cli.py                              # bcv-ingest (contrato público)
├── tests/
│   ├── unit/ · integration/ · e2e/
│   └── fixtures/2_1_2a20_smc.xls           # archivo oficial real (2020-TI, caso CHF)
└── gates/
    ├── gate-0-requirements.md
    ├── gate-1-design.md
    └── gate-2-implementation.md
```

## Modelo de datos fuente

Archivos oficiales `2_1_2*_smc.xls` del BCV: una hoja por fecha de operación (`DDMMYYYY`), ~23 monedas por hoja, cotizaciones BID/ASK en M.E./US$ y en Bs./M.E., con fecha de operación y fecha valor. Ver `docs/00-project/glossary.md`.
