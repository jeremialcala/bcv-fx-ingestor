# ADR-0006: Despliegue multinube edge-first — K8s CronJob + artefacto distribuido

* **Estado:** accepted
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 05-deployment
* **Versión:** 1.0.0
* **ID:** ADR-0006
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A02 (TLS/egress), A05 (configuración segura), A08 (integridad del artefacto)

## Contexto

El usuario quiere operar la ingesta fuera de su máquina, con compatibilidad AWS/GCP y
presencia edge en Cloudflare. Restricciones heredadas: el PRD declara la API de consulta
como **no-scope**; la ingesta es Python + xlrd + SQLite (no ejecutable en el runtime de
Workers); el charter deja el scheduling "en manos del operador vía cron"; ADR-0004 exige
TLS de fallo cerrado.

## Decisión

Un solo modelo de ejecución y una distribución multinube del resultado:

1. **Imagen única** (`ghcr.io/jeremialcala/bcv-fx-ingestor`, no-root, TLS estricto con el
   intermedio público de Sectigo vendorizado porque el portal envía cadena incompleta y
   OpenSSL no hace AIA — la verificación sigue siendo estricta).
2. **K8s CronJob** (kustomize: base + overlays `eks`/`gke`, solo cambia la storageClass y
   el mecanismo de credenciales — IRSA / Workload Identity). El CronJob es la
   materialización del "cron del operador" del charter, no un scheduler nuevo. Semántica
   fail-closed: si la ingesta falla (exit ≥ 3), el contenedor de publicación no corre.
3. **Publicación del artefacto con rclone** a S3, GCS y R2 (una herramienta, tres nubes;
   buckets versionados = rollback de datos).
4. **Edge = distribución, no API**: un Worker de Cloudflare sirve `bcv_fx.db` y `/estado`
   desde R2 con caché. Los analistas consumen el archivo SQLite completo, igual que en el
   diseño original.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| K8s CronJob + overlays (elegida) | Un modelo portable; manifests escaneables (IaC); fail-closed natural | Requiere un clúster disponible | Bajo: pod no-root, sin token de SA, egress solo al BCV y buckets |
| Serverless jobs (ECS Fargate + Cloud Run) | Sin clúster | Dos definiciones distintas + una tercera para el schedule; menos portable | Comparable, más superficie de configuración |
| Worker como API de consulta (D1) | Datos consultables en el edge | **Viola el no-scope del PRD**; reimplementa el dominio en JS; doble fuente de verdad | Superficie de red nueva sin threat model |
| Ingesta en Workers | "Todo edge" | xlrd/sqlite3/archivo .db no encajan en el runtime | Inviable |
| GitOps (ArgoCD/Flux) | Drift-detection de manifests | Otra pieza que operar para 1 CronJob | Desproporcionado hoy |

## Consecuencias

- Positivas: el operador elige nube con un `kubectl apply -k`; el artefacto queda replicado
  en tres proveedores (el modo local del ADR-0002 se beneficia: cualquier réplica sirve de
  respaldo); el edge da distribución global sin abrir superficie de consulta.
- Negativas / deuda asumida: el tag de imagen del CronJob se actualiza a mano en el
  manifest (sin GitOps); el intermedio de Sectigo vendorizado hay que rotarlo si el BCV
  cambia de CA (documentado en `deploy/docker/ca-extra/README.md`).
- Impacto en threat model: T2 conserva el fallo cerrado dentro del contenedor; T8 gana
  mitigación (réplicas del artefacto en tres nubes); la integridad del artefacto publicado
  queda trazable (sha256 en metadata, RS04).
