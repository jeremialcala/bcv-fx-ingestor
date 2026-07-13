# Observabilidad — BCV FX Ingestor

* **Estado:** review
* **Fecha:** 2026-07-12
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 06-monitoring
* **Versión:** 1.0.0
* **Gate:** 5
* **SLOs (ref):** tabla §SLIs y SLOs de este documento
* **On-call:** Operador de datos (charter, `<TODO: confirmar>` stakeholder)

Dimensionado al sistema real: un batch diario (CronJob) + distribución de un artefacto, no un
servicio 24/7. No hay stack de telemetría dedicado (Prometheus/Grafana sería desproporcionado
para un Job de 0.04 s/archivo — decisión consciente): las señales nacen de piezas que ya
existen y el canal de alerta es el email de workflow fallido de GitHub Actions.

## SLIs y SLOs

| SLI | SLO | Fuente de la señal | Alerta |
|---|---|---|---|
| Frescura del artefacto publicado (edad de `subido`) | ≤ 4 días naturales | Worker `GET /estado` | `health.yml` (mar–sáb) → email al fallar |
| Drift de la fuente (layout, URLs, TLS del portal) | smoke semanal verde | `smoke.yml` (ingesta real 2020-TI) | email al fallar |
| Éxito de la ingesta programada | ≥ 95 % de corridas/mes | historial de Jobs K8s (`kubectl -n bcv-fx get jobs`) | Job `Failed` → runbook |
| Cuarentenas pendientes | revisadas en ≤ 5 días hábiles | `bcv-ingest estado` (bloques `frescura` y `cuarentenas`) | revisión del operador |
| Pipeline de seguridad | CI verde en main + re-scan semanal (lunes) | Actions / badge | email al fallar |
| Duración de la corrida | < 15 min | `activeDeadlineSeconds: 900` en el CronJob | Job `DeadlineExceeded` |

El SLI de frescura tiene doble medición: en el edge (`/estado` del Worker, lo que ve el
analista) y en origen (`bcv-ingest estado` → `frescura.dias_desde_ultima_jornada`, lo que ve
el operador). Divergencia entre ambos = fallo de publicación, no de ingesta.

## Dónde nace cada señal (eje estructura)

```mermaid
C4Deployment
    title Puntos de telemetría — BCV FX Ingestor

    Person(operador, "Operador de datos", "On-call; recibe los emails de Actions")

    Deployment_Node(cluster, "Clúster K8s", "namespace bcv-fx") {
        Container(cron, "CronJob ingesta-bcv", "Python", "Señales: exit code, logs estructurados a stderr (WARNING por cuarentena, RS04), historial de Jobs")
        ContainerDb(pvc, "PVC /data", "bcv_fx.db", "Señal: bcv-ingest estado (frescura, totales, cuarentenas)")
    }

    Deployment_Node(edge, "Cloudflare", "edge global") {
        Container(worker, "Worker /estado", "JS + R2", "Señal: publicado, bytes, subido, sha256")
    }

    Deployment_Node(github, "GitHub Actions", "SaaS") {
        Container(health, "health.yml", "mar-sáb 12:00 UTC", "Vigila la frescura del artefacto vía /estado")
        Container(smoke, "smoke.yml", "lunes 06:00 UTC", "Ingesta real 2020-TI: drift T1/T2/T8")
        Container(ci, "ci.yml", "push + lunes 07:00 UTC", "Gates de seguridad; re-scan semanal de CVEs")
    }

    Rel(cron, pvc, "escribe BD y logs", "I/O")
    Rel(health, worker, "GET /estado", "HTTPS")
    Rel(health, operador, "email si falla", "GitHub")
    Rel(smoke, operador, "email si falla", "GitHub")
    Rel(ci, operador, "email si falla", "GitHub")
    Rel(operador, cron, "kubectl logs / get jobs", "kubectl")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="2")
```

## De la señal a la acción (eje comportamiento)

```mermaid
sequenceDiagram
    autonumber
    participant K as CronJob K8s
    participant R as Bucket R2
    participant W as Worker /estado
    participant GH as GitHub Actions
    participant O as Operador (on-call)

    Note over K: días hábiles 21:00 UTC
    K->>K: ingesta del trimestre (exit 0/2 éxito, >=3 falla)
    K->>R: publica bcv_fx.db (solo si la ingesta terminó bien)
    GH->>W: health (mar-sáb): GET /estado
    W->>R: head del artefacto
    alt artefacto fresco (<= 4 días)
        GH-->>GH: corrida verde (sin ruido)
    else viejo, no publicado o Worker caído
        GH-->>O: email de workflow fallido
        O->>K: kubectl -n bcv-fx get jobs · logs (runbook)
    end
    GH->>GH: smoke (lunes): ingesta real 2020-TI
    GH-->>O: email si hay drift del portal (T1/T2/T8)
    O->>O: bcv-ingest estado → frescura y cuarentenas pendientes
```

### Ciclo de vida del incidente

```mermaid
stateDiagram-v2
    [*] --> Detectado: email de Actions, Job Failed o cuarentenas crecen
    Detectado --> EnTriage: operador confirma la señal (runbook §matriz)
    EnTriage --> FalsaAlarma: no reproducible o transitorio del portal
    EnTriage --> Mitigado: acción del runbook aplicada
    Mitigado --> Resuelto: causa raíz corregida y SLO restablecido
    Resuelto --> Postmortem: hallazgo documentado en CHANGELOG / ADR / threat model
    Postmortem --> [*]
    FalsaAlarma --> [*]
```

Regla del postmortem: todo incidente real deja traza en el repo — como ya ocurrió dos veces en
este proyecto (cadena TLS incompleta → ADR-0004 §Nota + intermedio vendorizado; falsos
positivos ANG/BOB → RF04 recalibrado con umbral 1.25). El proceso no es aspiracional: está
ejercitado.

## Matriz señal → diagnóstico → acción (runbook de incidentes)

| Señal | Diagnóstico probable | Acción |
|---|---|---|
| `health.yml` rojo: Worker no responde | Worker caído o binding R2 roto | `npx wrangler deploy` / `wrangler rollback`; verificar bucket R2 |
| `health.yml` rojo: artefacto > 4 días | CronJob no corre o publicación falla | `kubectl -n bcv-fx get cronjob,jobs`; logs del initContainer (ingesta) y del contenedor `publicar` (rclone/credenciales) |
| Job fallido con exit ≥ 3 | red o TLS contra el portal (T2/T8) | ver logs: si es `CERTIFICATE_VERIFY_FAILED`, ¿rotó la CA del BCV? → actualizar `deploy/docker/ca-extra/`; si es indisponibilidad → modo local (ADR-0002) |
| `smoke.yml` rojo | drift del portal: layout (T1), patrón de URLs o TLS | comparar anclas del lector contra un archivo recién descargado; actualizar contrato de anclas / patrón y correr la suite |
| `cuarentenas_pendientes` crece | anomalías nuevas de la fuente (T3) | `bcv-ingest estado`; revisar `payload_crudo`; si es patrón legítimo nuevo → recalibrar validador con test de regresión (precedente ANG/BOB) |
| CI rojo en re-scan del lunes | CVE nueva en dependencia o imagen | actualizar la dependencia/base y re-correr; el pin de actions se revisa con el mismo email |
| Job `DeadlineExceeded` | corrida > 15 min (anómalo: lo normal es < 1 s/archivo) | logs del pod; ¿portal lento (T8)? reintentar; si persiste, modo local |

## Monitoreo de seguridad (OWASP A09)

- **Auditoría de decisiones**: cada cuarentena emite `WARNING` estructurado con archivo,
  sha256, hoja y motivo (RS04) — visible en `kubectl logs` y persistido en la tabla
  `cuarentena` con `payload_crudo`.
- **Integridad del artefacto**: sha256 por archivo ingerido (tabla `ingesta`) y `/estado`
  expone el hash del artefacto publicado.
- **Vigilancia continua**: gitleaks en cada push (historia completa), SCA + container scan
  re-corren cada lunes aunque no haya cambios, smoke vigila la superficie externa real.

## Hitos del proyecto (eje trazabilidad)

```mermaid
timeline
    title Del charter al release productivo
    2026-07-11 : v0.1.0 — Gate 0, requisitos y caso CHF documentado
               : v0.2.0 — Gate 1, diseño, threat model y decisión TLS de fallo cerrado
    2026-07-12 : v0.3.0 — Gate 2, ingestor completo y corpus 2020-2026 (30.784 tasas)
               : v0.4.0 — Gate 3, 78 tests, RF04 recalibrado con datos reales
               : v0.5.0 — Gate 4, CI con gates de seguridad, imagen GHCR, K8s y edge
               : v1.0.0 — Gate 5, SLOs monitorizados y proceso de incidentes (este corte)
```
