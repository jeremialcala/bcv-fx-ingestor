# Clasificación de Datos

* **Estado:** approved
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 00-project
* **Versión:** 0.1.0
* **Owner de datos (DPO):** Jeremi Alcalá
* **Regulación aplicable:** Ninguna (datos públicos oficiales; sin PII)

| Dato | Clasificación | Regulación | Cifrado en reposo | Cifrado en tránsito | Retención |
| --- | --- | --- | --- | --- | --- |
| Tasas de cambio de referencia (BID/ASK por moneda y jornada) | Público | — | No requerido | HTTPS en descarga | Indefinida (serie histórica) |
| Archivos SMC originales (`.xls`) | Público | — | No requerido | HTTPS en descarga | Indefinida (evidencia de origen) |
| Hash SHA-256 y metadatos de ingesta | Interno | — | No requerido | N/A (local) | Indefinida (auditoría) |
| Logs de ejecución y motivos de cuarentena | Interno | — | No requerido | N/A (local) | ≥ 1 año |
| Metadatos de autoría embebidos en los XLS (nombres de funcionarios BCV) | Interno | — | No requerido | N/A | No extraer ni almacenar |

Niveles: Público < Interno < Confidencial < Restringido.

Nota: aunque los datos son públicos, su **integridad** es el activo a proteger — una serie histórica corrupta produce decisiones financieras erróneas. Los controles del threat model priorizan integridad y trazabilidad sobre confidencialidad. Los archivos fuente traen metadatos OLE con nombres de personas (autor/último guardado); el proceso no los persiste.
