# ADR-0001: SQLite como almacén de la serie histórica

* **Estado:** accepted
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 1.0.0
* **ID:** ADR-0001
* **Supersede / Superseded-by:** —
* **Controles OWASP afectados:** A03 (inyección), A08 (integridad)

## Contexto

RF05 exige carga idempotente y consulta local de una serie de tamaño modesto (~250 jornadas/año × ~23 monedas ≈ 6.000 filas/año). El sponsor fijó el stack Python + SQLite. Un solo usuario/proceso escritor; consumo analítico local.

## Decisión

SQLite como único almacén, con constraints (`UNIQUE`, `CHECK`, FK) como línea de defensa de integridad, acceso exclusivamente vía `sqlite3` con queries parametrizadas, y `PRAGMA foreign_keys = ON`.

## Alternativas consideradas

| Opción | Pros | Contras | Riesgo de seguridad |
|---|---|---|---|
| SQLite (elegida) | Cero operación, archivo portable, constraints suficientes, stdlib | Concurrencia de escritura limitada | Bajo: superficie mínima, sin red |
| PostgreSQL | Concurrencia, tipos ricos | Requiere servidor; sobredimensionado para volumen y un solo escritor | Superficie de red añadida |
| DuckDB | Excelente para analítica | Menos maduro para cargas transaccionales idempotentes; fuera del stack fijado | Bajo |
| CSV/Parquet planos | Simplicidad | Sin constraints: la idempotencia queda solo en código (viola RS05) | Integridad débil |

## Consecuencias

- Positivas: despliegue trivial; la BD es un entregable portable; constraints hacen imposible el duplicado silencioso.
- Negativas / deuda asumida: si aparece un consumidor concurrente pesado, habrá que migrar (los puertos del núcleo lo aíslan).
- Impacto en threat model: elimina amenazas de red del almacén; T6 se mitiga por parametrización.
