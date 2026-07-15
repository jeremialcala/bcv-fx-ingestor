# Historial de implementación — BCV FX Ingestor

* **Estado:** approved
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 03-implementation
* **Versión:** 1.2.0
* **Gate:** 2
* **Rama principal:** main
* **Estrategia de branching:** gitflow (develop/feature/release; trunk-based hasta v1.0.0)

## Historial del repositorio (documentación viva)

Derivado de `git log` con `scripts/gitgraph_from_log.py`. Regenerar tras cada merge o tag para
mantener la traza sincronizada. Los tags SemVer enlazan con las versiones del `CHANGELOG.md`.

### Grafo de commits y merges

```mermaid
gitGraph
    commit id: "6bec837" tag: "v0.1.0"
    commit id: "d478480"
    commit id: "da80218"
    commit id: "cbf7f80" tag: "v0.2.0"
    commit id: "2c1957a"
    commit id: "cf80831"
    commit id: "5c1ab67"
    commit id: "41a107d" tag: "v0.3.0"
    commit id: "da1582f"
    commit id: "23d47f4"
    commit id: "95ea337"
    commit id: "883d24f"
    commit id: "65df9a3"
    commit id: "631d848" tag: "v0.4.0"
    commit id: "90f6cdd"
    commit id: "f036dd8"
    commit id: "d7993b1"
    commit id: "c24f27d"
    commit id: "f679b03"
    commit id: "5400c96"
    commit id: "8e38251"
    commit id: "cc9dc5e" tag: "v0.5.0"
    commit id: "4b2c7f7"
    commit id: "cbb49ed"
    commit id: "40b6595"
    commit id: "be0efd3" tag: "v1.0.0"
    commit id: "5e31f39"
    commit id: "684afd8"
    commit id: "b54ac5b"
    commit id: "5238f3f"
    branch feature-0
    checkout feature-0
    commit id: "1482c54"
    commit id: "2c954ca"
    commit id: "2fde888"
    checkout main
    merge feature-0 tag: "v1.1.0"
    branch feature-1
    checkout feature-1
    commit id: "b7497c0"
    commit id: "66c2183"
    commit id: "01f34f3"
    commit id: "37f4f54"
    commit id: "0ea51a9"
    checkout main
    merge feature-1 tag: "v1.2.0"
```

### Bitácora de cambios (fiel al repo)

| Commit | Tipo | Tags | Autor | Fecha | Mensaje |
|---|---|---|---|---|---|
| `1d10141` | merge | — | Jeremi Alcala | 2026-07-14 | Merge release/1.2.0 en develop — cierre de la release 1.2.0 |
| `dbd53e5` | merge | v1.2.0 | Jeremi Alcala | 2026-07-14 | Merge release/1.2.0 en main — versión 1.2.0 (Gate 1 de FX-ING-002) |
| `0ea51a9` | commit | — | Jeremi Alcala | 2026-07-14 | chore(release): cortar versión 1.2.0 — Gate 1 de FX-ING-002 |
| `37f4f54` | merge | — | Jeremi Alcala | 2026-07-14 | Merge feature/fx-ing-002-diseno en develop — fase 02-design del feature FX-ING-002 |
| `01f34f3` | commit | — | Jeremi Alcala | 2026-07-14 | feat(fx-ing-002): fase 02-design — consulta en el edge con JSON precalculado |
| `66c2183` | commit | — | Jeremi Alcala | 2026-07-14 | docs: regenerar historial vivo tras el tag v1.1.0 — gitflow adoptado |
| `d75331c` | merge | v1.1.0 | Jeremi Alcala | 2026-07-14 | Merge release/1.1.0 en main — versión 1.1.0 (Gate 0 de FX-ING-002) |
| `b7497c0` | merge | — | Jeremi Alcala | 2026-07-14 | Merge release/1.1.0 en develop — cierre de la release 1.1.0 |
| `2fde888` | commit | — | Jeremi Alcala | 2026-07-14 | chore(release): cortar versión 1.1.0 — Gate 0 de FX-ING-002 |
| `2c954ca` | merge | — | Jeremi Alcala | 2026-07-14 | Merge feature/fx-ing-002-requisitos en develop — Gate 0 del feature FX-ING-002 |
| `1482c54` | commit | — | Jeremi Alcala | 2026-07-14 | feat(fx-ing-002): requisitos de consulta y descarga vía Web UI y API — Gate 0 aprobado |
| `5238f3f` | commit | — | Jeremi Alcala | 2026-07-12 | fix(deploy): securityContext explícito en el patch local para el escaneo IaC |
| `b54ac5b` | commit | — | Jeremi Alcala | 2026-07-12 | chore: excluir el estado local de wrangler (.wrangler/) del repositorio |
| `684afd8` | commit | — | Jeremi Alcala | 2026-07-12 | feat(deploy): overlay local (kind/docker-desktop) verificado end-to-end |
| `5e31f39` | commit | — | Jeremi Alcala | 2026-07-12 | docs: regenerar historial vivo tras el tag v1.0.0 — ciclo AI-DLC completo |
| `be0efd3` | commit | v1.0.0 | Jeremi Alcala | 2026-07-12 | docs: aprobar Gate 5 y cortar versión 1.0.0 — primer release productivo |
| `40b6595` | commit | — | Jeremi Alcala | 2026-07-12 | feat: fase 06-monitoring hacia el Gate 5 — SLOs monitorizados y proceso de incidentes |
| `cbb49ed` | commit | — | Jeremi Alcala | 2026-07-12 | chore(ci): actualizar actions a majors con Node 24 |
| `4b2c7f7` | commit | — | Jeremi Alcala | 2026-07-12 | docs: regenerar historial vivo tras el tag v0.5.0 |
| `cc9dc5e` | commit | v0.5.0 | Jeremi Alcala | 2026-07-12 | docs: aprobar Gate 4 y cortar versión 0.5.0 |
| `8e38251` | commit | — | Jeremi Alcala | 2026-07-12 | docs: registrar la corrida verde del smoke como evidencia del Gate 4 |
| `5400c96` | commit | — | Jeremi Alcala | 2026-07-12 | fix(ci): instalar el intermedio de Sectigo en el runner del smoke |
| `f679b03` | commit | — | Jeremi Alcala | 2026-07-12 | docs: registrar la corrida verde del CI como evidencia del Gate 4 |
| `c24f27d` | commit | — | Jeremi Alcala | 2026-07-12 | docs: reaplicar cabecera y trazabilidad al historial vivo |
| `d7993b1` | commit | — | Jeremi Alcala | 2026-07-12 | fix(ci): corregir referencia de trivy-action y regenerar historial vivo |
| `f036dd8` | commit | — | Jeremi Alcala | 2026-07-12 | feat: fase 05-deployment — CI con gates de seguridad y despliegue multinube edge-first |
| `90f6cdd` | commit | — | Jeremi Alcala | 2026-07-12 | docs: regenerar historial vivo tras el tag v0.4.0 |
| `631d848` | commit | v0.4.0 | Jeremi Alcala | 2026-07-12 | docs: aprobar Gate 3 y cortar versión 0.4.0 |
| `65df9a3` | commit | — | Jeremi Alcala | 2026-07-12 | test: cerrar las brechas de la evaluación del Gate 3 |
| `883d24f` | commit | — | Jeremi Alcala | 2026-07-12 | test: fase 04-testing hacia el Gate 3 — estrategia, matriz de transiciones y trazabilidad requisito↔test. |
| `95ea337` | commit | — | Jeremi Alcala | 2026-07-12 | fix: recalibrar la regla de coherencia de spread de RF04 contra el corpus completo |
| `23d47f4` | commit | — | Jeremi Alcala | 2026-07-12 | chore: excluir .coverage del repositorio |
| `da1582f` | commit | — | Jeremi Alcala | 2026-07-12 | docs: auditoría AI-DLC — documentación viva de fase 03, versiones sincronizadas y hallazgos SAST corregidos |
| `41a107d` | commit | v0.3.0 | Jeremi Alcala | 2026-07-12 | docs: aprobar Gate 2 y cortar versión 0.3.0 |
| `5c1ab67` | commit | — | Jeremi Alcala | 2026-07-12 | feat: implementación de la fase 03 — ingestor completo con CLI y pirámide de tests |
| `cf80831` | commit | — | Jeremi Alcala | 2026-07-12 | docs: mejorar claridad y formato en la sección de alcance del proyecto |
| `2c1957a` | commit | — | Jeremi Alcala | 2026-07-12 | docs: corregir formato de tabla en la clasificación de datos |
| `cbf7f80` | commit | v0.2.0 | Jeremi Alcala | 2026-07-11 | docs: aprobar gates 0 y 1 y cortar versión 0.2.0 |
| `da80218` | commit | — | Jeremi Alcala | 2026-07-11 | docs: actualizar changelog y documentación sobre política TLS estricta sin excepciones |
| `d478480` | commit | — | Jeremi Alcala | 2026-07-11 | docs: confirmar patrón de URLs de descarga del BCV |
| `6bec837` | commit | v0.1.0 | Jeremi Alcala | 2026-07-11 | docs: documentación inicial AI-DLC (fases 00–02, gates 0 y 1 en review) |

## Trazabilidad tag ↔ versión ↔ decisión

| Tag | Versión CHANGELOG | ADR / feature | Nota |
|---|---|---|---|
| v0.1.0 | 0.1.0 (Gate 0) | FX-ING-001 (PRD) | charter, glosario, clasificación de datos, PRD |
| v0.2.0 | 0.2.0 (Gate 1) | ADR-0001 · ADR-0002 · ADR-0003 · ADR-0004 | diseño, threat model, patrón de URLs confirmado, decisión TLS |
| v0.3.0 | 0.3.0 (Gate 2) | ADR-0002/0003/0004 implementadas | ingestor completo, RF04 refinado (spread entre bases), truststore |
| v0.4.0 | 0.4.0 (Gate 3) | FX-ING-001 verificada (RF/RNF/RS ↔ tests) | estrategia de pruebas, matriz de transiciones, RF04 recalibrado con el corpus, 78 tests / 99% |
| v0.5.0 | 0.5.0 (Gate 4) | ADR-0005 · ADR-0006 | CI con gates de seguridad, imagen GHCR, K8s EKS/GKE, Worker R2; intermedio Sectigo vendorizado |
| v1.0.0 | 1.0.0 (Gate 5) | observability.md (SLOs + incidentes) | primer release productivo: frescura instrumentada, health/smoke/re-scan como alertas — ciclo AI-DLC completo |
| v1.1.0 | 1.1.0 (Gate 0 de FX-ING-002) | FX-ING-002 (PRD consulta-descarga) · ADR-0007 pendiente | requisitos de consulta y descarga vía Web UI y API con clave API; no-scope levantado; overlay k8s local; adopción de gitflow |
| v1.2.0 | 1.2.0 (Gate 1 de FX-ING-002) | ADR-0007 · ADR-0008 · openapi-consulta.yaml | diseño del edge: JSON precalculado junto al artefacto, rate limiting en plataforma, STRIDE/DREAD T9–T15 |
