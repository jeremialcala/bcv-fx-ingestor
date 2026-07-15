# ADR-0008: Rate limiting en la plataforma Cloudflare con topes de respuesta en el Worker

* **Estado:** accepted
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0008
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A04 (diseño inseguro / anti-automatización), A01 (control de acceso)

## Contexto

RS09 (ASVS V11.1, Gate 0 de FX-ING-002) exige anti-automatización para la superficie de consulta: la amenaza T11 (scraping masivo / DoS que degrada el servicio y dispara costos del edge) es la más probable del DREAD del feature. Hay dos lugares donde puede vivir el límite: la plataforma (reglas de rate limiting de Cloudflare, por IP) o el propio Worker (contadores por clave API, que requieren estado — Durable Objects o KV).

## Decisión

Anti-automatización en dos capas, **sin estado propio**:

1. **Plataforma:** regla de rate limiting de Cloudflare sobre la ruta `/api/*` (por IP, umbral y ventana configurados en el despliegue; disponible incluso en el plan free). Responde 429 antes de ejecutar el Worker — el abuso ni siquiera consume invocaciones.
2. **Worker:** topes estructurales por request — `limite` máximo de 1.000 filas por página (RNF07), tamaño de respuesta acotado, rango de fechas máximo por consulta de serie. Nunca se construyen respuestas sin cota.

El límite fino **por clave API** se cubre con los controles existentes, no con contadores: auditoría de uso por identificador de clave (RS11) para detectar abuso, y revocación/rotación de la clave (RS07) como respuesta. Si el volumen de consumidores crece y la revocación deja de bastar, se revisará esta ADR (Durable Objects por clave).

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| Reglas de plataforma + topes en el Worker (elegida) | Sin estado ni costo adicional; corta el abuso antes del Worker; simple de operar | Límite por IP, no por clave (IPs compartidas/NAT pueden penalizar a legítimos; un botnet distribuido lo evade parcialmente) | Residual bajo: los topes del Worker acotan el daño por request |
| Contadores por clave en el Worker (Durable Objects/KV) | Límite fino por credencial; cuotas diferenciadas | Estado distribuido, costo por operación, complejidad de expiración/ventanas; sobredimensionado para ~unidades de consumidores | Un bug en el contador se convierte en DoS propio o en bypass |
| Solo topes en el Worker (sin regla de plataforma) | Cero configuración de zona | Cada request abusivo ejecuta el Worker igual (costo por invocación persiste) | T11 solo parcialmente mitigada |

## Consecuencias

- Positivas: T11 tiene control en la capa más barata; RS09 queda trazable a configuración de plataforma + código del Worker; el diseño no introduce estado nuevo en el edge.
- Negativas / deuda asumida: el umbral por IP se configura fuera del repo (dashboard/API de Cloudflare) — el runbook de despliegue debe documentarlo y verificarlo (se añade a `deployment.md` en la fase de implementación); sin límite per-clave hasta que el volumen lo justifique.
- Impacto en threat model: T11 pasa a mitigada (plataforma + topes); T9 (clave robada) conserva como respuesta la revocación + auditoría, no el throttling.
