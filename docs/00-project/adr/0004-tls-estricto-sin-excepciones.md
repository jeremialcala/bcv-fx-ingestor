# ADR-0004: Verificación TLS estricta sin mecanismo de excepción

* **Estado:** accepted
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0004
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A02 (fallas criptográficas), A08 (integridad)

## Contexto

El threat model prioriza T2 (suplantación del portal BCV / MITM en descarga, DREAD 6.4). El portal ha presentado históricamente certificados TLS inválidos (charter, riesgo R4), lo que planteaba la disyuntiva: fallar siempre, o permitir una excepción explícita (`--inseguro`) con registro. Evidencia del 2026-07-11: el certificado actual de `www.bcv.org.ve` valida correctamente contra el almacén de confianza del sistema. Decisión HITL requerida por el Gate 1 (criterio 9), tomada por Jeremi Alcalá el 2026-07-11.

## Decisión

Verificación TLS estricta con fallo cerrado: ante cualquier certificado inválido del portal BCV, la descarga falla y la ingesta por descarga se aborta con error explícito. No existe flag `--inseguro` ni ninguna otra vía de excepción en el código. Si el portal presenta un certificado inválido, la vía operativa es el modo local (ADR-0002): el operador obtiene el archivo por un canal que valide por sus propios medios y lo coloca en la carpeta de entrada, quedando `ingesta.origen = local` como traza de que la descarga automática no intervino.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| Fallo cerrado sin excepciones (elegida) | Elimina T2 en la vía de descarga; imposible de degradar por error u operador apurado | Descarga bloqueada mientras el portal tenga certificado inválido | Mínimo |
| Flag `--inseguro` + registro | Continuidad operativa sin pasos manuales | La excepción se normaliza con el uso; superficie real para MITM | Alto |
| Pinning del certificado del BCV | Protege incluso ante CA comprometida | Rompe con cada rotación del certificado del portal; carga de mantenimiento | Medio |

## Consecuencias

- Positivas: el control de T2 pasa de "excepción solo HITL" a "sin excepción"; el descargador no contiene rutas inseguras que auditar ni configurar.
- Negativas / deuda asumida: si el portal vuelve a presentar certificado inválido por un período prolongado, toda ingesta nueva requiere el paso manual del modo local.
- Impacto en threat model: T2 queda mitigado en la vía descarga; el riesgo residual se desplaza al procedimiento manual del operador, cubierto por el pipeline único (hash SHA-256 + validaciones idénticas, ADR-0002).
