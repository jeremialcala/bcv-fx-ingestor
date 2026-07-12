# ADR-0005: CI en GitHub Actions con los gates de seguridad de AI-DLC

* **Estado:** accepted
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 05-deployment
* **Versión:** 1.0.0
* **ID:** ADR-0005
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A03 (SAST), A06 (SCA/container), A05 (IaC), A09 (evidencia auditable)

## Contexto

Todos los checks de calidad y seguridad del proyecto (pytest, bandit, pip-audit, validación
Mermaid) existían pero corrían solo en la máquina del desarrollador: sin evidencia
reproducible por commit ni bloqueo automático. El repo ya vive en GitHub y la fase 05 exige
un pipeline con los gates de seguridad de la metodología (SAST, SCA, secrets, license,
container, IaC, DAST) y publicación de la imagen del contenedor.

## Decisión

GitHub Actions como CI (`.github/workflows/ci.yml`): 8 jobs paralelos — tests (matriz
3.11/3.12, cobertura ≥ 90%), sast (bandit), sca (pip-audit), secrets (gitleaks), license
(pip-licenses con allowlist), docs (Mermaid con script vendorizado), container (build +
Trivy image; en tags publica a GHCR verificando tag == `pyproject.version`) e iac
(kubeconform estricto + Trivy config). DAST se declara N/A con justificación (sin
superficie de red entrante). Un workflow aparte (`smoke.yml`, semanal, no bloqueante)
ingiere un trimestre real del portal para detectar drift de layout/URLs/TLS. Badges de
estado y de último tag en el README.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| GitHub Actions (elegida) | Nativo del repo, GHCR y OIDC integrados, gitleaks/trivy como actions maduras | Lock-in moderado al runner de GitHub | Bajo; permisos mínimos por job |
| GitLab CI / mirror | Pipelines potentes | Repo no vive ahí; duplicar remotes | Superficie extra |
| Jenkins autogestionado | Control total | Operar un servidor CI para una CLI es desproporcionado | El propio Jenkins como activo a proteger |
| Solo checks locales (statu quo) | Cero infraestructura | Sin evidencia por commit; el gate depende de disciplina manual | Regresiones de seguridad silenciosas |

## Consecuencias

- Positivas: cada push/PR deja evidencia verificable de los gates; los tags publican imagen
  reproducible; el smoke semanal vigila el drift de la fuente sin intervención humana.
- Negativas / deuda asumida: acciones de terceros fijadas por major version (riesgo de
  supply-chain mitigado por `permissions: contents: read` por defecto y GITHUB_TOKEN de
  alcance mínimo); el smoke depende de la disponibilidad del portal BCV.
- Impacto en threat model: T1/T2/T8 ganan detección temprana (smoke); T6/T5 quedan
  vigilados por SAST/SCA en cada cambio.
