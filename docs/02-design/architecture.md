# Diseño del Sistema — BCV FX Ingestor

* **Estado:** review
* **Fecha:** 2026-07-11
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 0.1.0
* **Gate:** 1
* **Estilo arquitectónico:** Clean / hexagonal (puertos y adaptadores)
* **ADRs relacionadas:** ADR-0001, ADR-0002, ADR-0003

## Contextos acotados (DDD)

| Bounded Context | Responsabilidad | Entidades núcleo |
|---|---|---|
| Ingesta Cambiaria | Obtener, validar y cargar jornadas de tasas de referencia | Ingesta, Jornada, Tasa, Moneda |

## Vista C4 — Container

```mermaid
C4Container
    title Diagrama de contenedores — BCV FX Ingestor

    Person(operador, "Operador de datos", "Ejecuta comandos y resuelve cuarentenas")
    System_Ext(bcv, "Portal BCV", "Publica los archivos SMC", $tags="external")

    System_Boundary(ingestor, "BCV FX Ingestor") {
        Container(cli, "CLI bcv-ingest", "Python / argparse", "Comandos descargar, cargar, estado")
        Container(core, "Núcleo de ingesta", "Python puro", "Casos de uso, reglas de validación, entidades de dominio", $tags="principle")
        Container(entrada, "Carpeta de entrada", "Sistema de archivos", "XLS descargados o colocados manualmente", $tags="owasp-a08")
        ContainerDb(db, "Base histórica", "SQLite", "ingesta, jornada, tasa, moneda, cuarentena")
    }

    Rel(operador, cli, "Opera", "shell")
    Rel(cli, core, "Invoca casos de uso de", "llamada en proceso")
    Rel(core, bcv, "Descarga XLS de", "HTTPS con verificación TLS")
    Rel(core, entrada, "Lee y archiva XLS en", "I/O local")
    Rel(core, db, "Carga jornadas en", "sqlite3 parametrizado")

    UpdateElementStyle(core, $bgColor="#1168bd", $fontColor="#ffffff")
    UpdateElementStyle(bcv, $bgColor="#999999", $fontColor="#ffffff")
    UpdateElementStyle(entrada, $borderColor="#b30000")
    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Vista C4 — Component (núcleo de ingesta)

```mermaid
C4Component
    title Diagrama de componentes — Núcleo de ingesta

    Container_Ext(cli, "CLI bcv-ingest", "Python", "Punto de entrada")
    System_Ext(bcv, "Portal BCV", "Fuente externa", $tags="external")
    ContainerDb(db, "Base histórica", "SQLite", "Datos consolidados")

    Container_Boundary(core, "Núcleo de ingesta") {
        Component(usecases, "Casos de uso", "Python puro", "IngestarArchivo, DescargarPeriodo, ConsultarEstado")
        Component(descargador, "Descargador BCV", "httpx", "Adaptador HTTP: descarga con TLS verificado y reintentos", $tags="owasp-a02")
        Component(lector, "Lector XLS", "xlrd", "Adaptador de parseo del layout SMC; trata el archivo como entrada no confiable", $tags="owasp-a03")
        Component(validador, "Validador de dominio", "Python puro", "BID<=ASK, positivos, moneda conocida, fechas coherentes, escala", $tags="principle")
        Component(repo, "Repositorio de tasas", "sqlite3", "Persistencia idempotente con constraints y queries parametrizadas", $tags="owasp-a08")
    }

    Rel(cli, usecases, "Invoca")
    Rel(usecases, descargador, "Usa")
    Rel(usecases, lector, "Usa")
    Rel(usecases, validador, "Usa")
    Rel(usecases, repo, "Usa")
    Rel(descargador, bcv, "GET archivos SMC", "HTTPS")
    Rel(repo, db, "Lee/escribe", "SQL parametrizado")

    UpdateElementStyle(usecases, $bgColor="#1168bd", $fontColor="#ffffff")
    UpdateElementStyle(lector, $borderColor="#b30000")
    UpdateElementStyle(descargador, $borderColor="#b30000")
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

Dirección de dependencias (Clean Architecture): `cli → usecases → puertos`; `descargador`, `lector` y `repo` implementan puertos definidos por el núcleo. El dominio no importa xlrd, httpx ni sqlite3.

## Flujos críticos (comportamiento)

```mermaid
sequenceDiagram
    autonumber
    actor O as Operador
    participant C as CLI
    participant U as Casos de uso
    participant D as Descargador BCV
    participant B as Portal BCV
    participant L as Lector XLS
    participant V as Validador
    participant R as Repositorio SQLite
    O->>C: bcv-ingest descargar --desde 2020-01 --hasta 2020-12
    C->>U: DescargarPeriodo(rango)
    U->>D: obtener(periodo)
    D->>B: GET 2_1_2a20_smc.xls (HTTPS verificado)
    B-->>D: archivo XLS
    D-->>U: ruta + SHA-256
    U->>R: hash ya ingerido?
    alt hash conocido
        R-->>U: duplicado
        U-->>C: reporta "ya ingerido"
    else hash nuevo
        U->>L: parsear hojas DDMMYYYY
        L-->>U: jornadas + tasas crudas
        U->>V: validar reglas de dominio
        alt fila anómala (ej. BID > ASK)
            V-->>U: motivo de cuarentena
            U->>R: registrar en cuarentena
        else fila válida
            U->>R: upsert idempotente jornada+tasa
        end
        U-->>C: resumen: cargadas / duplicadas / cuarentena
    end
    C-->>O: reporte de ejecución
```

## Ciclo de vida de la entidad núcleo (Ingesta)

```mermaid
stateDiagram-v2
    [*] --> Detectado: archivo en carpeta o URL resuelta
    Detectado --> Obtenido: descarga o lectura local OK
    Detectado --> Fallido: error de red o I/O
    Obtenido --> Duplicado: SHA-256 ya registrado
    Obtenido --> Validando: hash nuevo, parseo iniciado
    Validando --> Cargado: todas las filas válidas cargadas
    Validando --> CargadoParcial: filas válidas cargadas, anómalas en cuarentena
    Validando --> Cuarentena: layout irreconocible o archivo corrupto
    Cuarentena --> Validando: reproceso tras decisión humana
    Cargado --> [*]
    CargadoParcial --> [*]
    Duplicado --> [*]
    Fallido --> [*]
```

## Modelo de datos y dominio

```mermaid
erDiagram
    INGESTA ||--o{ JORNADA : produce
    JORNADA ||--|{ TASA : contiene
    MONEDA ||--o{ TASA : cotiza
    INGESTA ||--o{ CUARENTENA : aparta
    INGESTA {
        int id PK
        string nombre_archivo
        string sha256 UK
        string origen "descarga | local"
        string estado
        datetime procesado_en
    }
    JORNADA {
        int id PK
        date fecha_operacion UK
        date fecha_valor
        datetime publicado_en
        int escala_monetaria "1, 1e5 (2018), 1e11 (2021)"
        int ingesta_id FK
    }
    TASA {
        int id PK
        int jornada_id FK
        int moneda_id FK
        real usd_bid
        real usd_ask
        real bs_bid
        real bs_ask
        bool cotizacion_invertida "EUR y GBP"
    }
    MONEDA {
        int id PK
        string codigo UK
        string pais
        bool es_iso4217 "MXP y CUC no lo son"
    }
    CUARENTENA {
        int id PK
        int ingesta_id FK
        string hoja
        string motivo
        string payload_crudo
    }
```

```mermaid
classDiagram
    class IngestarArchivoUseCase {
        +ejecutar(ruta) ResumenIngesta
    }
    class FuenteArchivosPort {
        <<interface>>
        +obtener(periodo) ArchivoSmc
    }
    class LectorTasasPort {
        <<interface>>
        +parsear(archivo) List~JornadaCruda~
    }
    class RepositorioTasasPort {
        <<interface>>
        +hashConocido(sha256) bool
        +guardarJornada(jornada) ResultadoCarga
        +enviarACuarentena(item) void
    }
    class ValidadorDominio {
        +validar(JornadaCruda) ResultadoValidacion
    }
    class DescargadorHttpBcv
    class CarpetaLocalAdapter
    class LectorXlsXlrd
    class RepositorioSqlite
    IngestarArchivoUseCase --> FuenteArchivosPort
    IngestarArchivoUseCase --> LectorTasasPort
    IngestarArchivoUseCase --> ValidadorDominio
    IngestarArchivoUseCase --> RepositorioTasasPort
    DescargadorHttpBcv ..|> FuenteArchivosPort
    CarpetaLocalAdapter ..|> FuenteArchivosPort
    LectorXlsXlrd ..|> LectorTasasPort
    RepositorioSqlite ..|> RepositorioTasasPort
```

## Contratos (CLI + schema SQLite)

No hay API de red: el contrato público es la CLI y el schema de la base.

| Comando | Argumentos | Salida / exit code |
|---|---|---|
| `bcv-ingest descargar` | `--desde AAAA-MM --hasta AAAA-MM [--destino DIR]` | Resumen JSON por archivo; 0 OK, 2 cuarentenas, 3 error de red |
| `bcv-ingest cargar` | `RUTA` (archivo `.xls` o carpeta) | Resumen JSON: cargadas/duplicadas/cuarentena; 0 OK, 2 cuarentenas |
| `bcv-ingest estado` | `[--jornada AAAA-MM-DD]` | Estado de ingestas y cuarentenas pendientes; 0 siempre |

```sql
CREATE TABLE ingesta (
  id INTEGER PRIMARY KEY,
  nombre_archivo TEXT NOT NULL,
  sha256 TEXT NOT NULL UNIQUE,
  origen TEXT NOT NULL CHECK (origen IN ('descarga','local')),
  estado TEXT NOT NULL,
  procesado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE moneda (
  id INTEGER PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE,
  pais TEXT NOT NULL,
  es_iso4217 INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE jornada (
  id INTEGER PRIMARY KEY,
  fecha_operacion TEXT NOT NULL UNIQUE,
  fecha_valor TEXT NOT NULL,
  publicado_en TEXT,
  escala_monetaria INTEGER NOT NULL DEFAULT 1,
  ingesta_id INTEGER NOT NULL REFERENCES ingesta(id),
  CHECK (fecha_valor >= fecha_operacion)
);
CREATE TABLE tasa (
  id INTEGER PRIMARY KEY,
  jornada_id INTEGER NOT NULL REFERENCES jornada(id),
  moneda_id INTEGER NOT NULL REFERENCES moneda(id),
  usd_bid REAL NOT NULL CHECK (usd_bid > 0),
  usd_ask REAL NOT NULL CHECK (usd_ask > 0),
  bs_bid REAL NOT NULL CHECK (bs_bid > 0),
  bs_ask REAL NOT NULL CHECK (bs_ask > 0),
  cotizacion_invertida INTEGER NOT NULL DEFAULT 0,
  UNIQUE (jornada_id, moneda_id)
);
CREATE TABLE cuarentena (
  id INTEGER PRIMARY KEY,
  ingesta_id INTEGER NOT NULL REFERENCES ingesta(id),
  hoja TEXT,
  motivo TEXT NOT NULL,
  payload_crudo TEXT,
  creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Nota: `BID <= ASK` se valida en el Validador (no como CHECK) porque la fuente contiene violaciones reales que deben ir a cuarentena con contexto, no fallar la transacción.

## Patrones de seguridad seleccionados (por amenaza DREAD priorizada)

| Amenaza | Patrón / Control | OWASP |
|---|---|---|
| T1 Cambio de layout silencioso | Parser con contrato explícito (posiciones + encabezados verificados); si no coincide → cuarentena, nunca "mejor esfuerzo" | A08 |
| T3 Datos fuente erróneos | Validación de dominio + cuarentena trazable (evidencia: CHF 31/03/2020) | A08 |
| T2 Suplantación de fuente | HTTPS con verificación estricta; hash SHA-256 registrado; excepción TLS solo por decisión humana documentada | A02 |
| T4 Re-ingesta duplicada/alterada | Idempotencia por constraints (UNIQUE sha256, UNIQUE jornada+moneda) | A08 |
| T5 XLS malicioso | xlrd sin macros; límites de tamaño/filas; ingesta en proceso sin privilegios | A03/A08 |
| T6 Inyección SQL | Solo queries parametrizadas (sqlite3 placeholders) | A03 |
| T7 Mezcla de escalas | Campo `escala_monetaria` por jornada + tabla de vigencia de redenominaciones | A08 |
