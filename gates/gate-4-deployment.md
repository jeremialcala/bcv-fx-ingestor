# Gate 4 — Deployment

* **Estado:** review
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 05-deployment
* **Versión:** 0.5.0

| # | Criterio | Evidencia | Estado |
|---|---|---|---|
| 1 | Pipeline CI con los gates de seguridad, limpio | `.github/workflows/ci.yml` (tests, sast, sca, secrets, license, docs, container, iac) — corrida verde: `<TODO: enlazar la corrida tras el push>` | ⬜ pendiente de la primera corrida |
| 2 | DAST | N/A justificado: sin superficie de red entrante; equivalente dinámico = `smoke.yml` semanal contra el portal real + tests de entrada hostil del Gate 3 | ✅ N/A |
| 3 | IaC escaneado | kubeconform estricto (base + 2 overlays: 3/3 válidos) + Trivy config (0 misconfiguraciones HIGH/CRITICAL) — local y como job `iac` | ✅ |
| 4 | Imagen de contenedor escaneada | Trivy image: 0 vulnerabilidades HIGH/CRITICAL con fix; no-root (uid 10001); verificada contra el portal real (descarga TLS estricta + ingesta dentro del contenedor) | ✅ |
| 5 | Runbook de despliegue y rollback | `deployment.md` §Runbook (inicial, actualización, rollback de imagen/datos/Worker, verificación post-deploy) | ✅ |
| 6 | Evidencia en 3 ejes | `deployment.md`: C4Deployment · flowchart pipeline+rollback · gantt cutover (Mermaid validado) | ✅ |
| 7 | Multinube + edge operables | Overlays EKS/GKE (kubeconform OK), Worker validado con `wrangler deploy --dry-run` (binding R2 correcto) | ✅ |
| 8 | ADRs de las decisiones | ADR-0005 (CI GitHub Actions), ADR-0006 (multinube edge-first; Worker-API rechazada por no-scope) | ✅ |
| 9 | Badges y CHANGELOG al día | README con badge de última ejecución del CI + último tag; `[Unreleased]` con la fase 05 | ✅ |
| 10 | **Aprobación humana del gate** | — | ⬜ pendiente (HITL) |

Hallazgo de la fase (documentado): dentro del contenedor Linux, OpenSSL no resuelve la cadena
incompleta del BCV vía AIA como Windows; la imagen vendoriza el intermedio público de Sectigo
(huella en `deploy/docker/ca-extra/README.md`) sin debilitar el fallo cerrado de ADR-0004.

Abierto trasladado desde el Gate 0: confirmar stakeholders operador/analista (charter).

Al aprobar: cortar `[Unreleased]` → `0.5.0` en CHANGELOG (sincronizando `pyproject.version`),
tag `v0.5.0` (publica la imagen a GHCR) y arrancar 06-monitoring (Gate 5 → 1.0.0).
