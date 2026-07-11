# bcv-fx-ingestor

Proceso de ingesta y carga de los tipos de cambio de referencia históricos del Banco Central de Venezuela (BCV) hacia SQLite, con CLI en Python.

Proyecto estructurado con la metodología **AI-DLC** (seguridad por diseño, gates con Human-in-the-Loop).

## Estado

| Fase | Gate | Estado |
|---|---|---|
| 00-project | — | approved |
| 01-requirements | Gate 0 | ✅ aprobado 2026-07-11 |
| 02-design | Gate 1 | ✅ aprobado 2026-07-11 |
| 03-implementation | Gate 2 | lista para arrancar |

## Estructura

```
bcv-fx-ingestor/
├── CHANGELOG.md
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
└── gates/
    ├── gate-0-requirements.md
    └── gate-1-design.md
```

## Modelo de datos fuente

Archivos oficiales `2_1_2*_smc.xls` del BCV: una hoja por fecha de operación (`DDMMYYYY`), ~23 monedas por hoja, cotizaciones BID/ASK en M.E./US$ y en Bs./M.E., con fecha de operación y fecha valor. Ver `docs/00-project/glossary.md`.
