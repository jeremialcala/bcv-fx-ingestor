# Diseño del Sistema — BCV FX Ingestor

* **Estado:** review
* **Fecha:** 2026-07-14
* **Decisores:** Jeremi Alcalá
* **Fase AI-DLC:** 02-design
* **Versión:** 0.3.0
* **Gate:** 1
* **Estilo arquitectónico:** Clean / hexagonal (puertos y adaptadores)
* **ADRs relacionadas:** ADR-0001, ADR-0002, ADR-0003, ADR-0007, ADR-0008

> *(Actualización 2026-07-14, FX-ING-002: se añade la vista de distribución y consulta en el edge — §Distribución y consulta. Las secciones de la ingesta permanecen como fueron aprobadas en el Gate 1 original; el doc vuelve a `review` hasta el Gate 1 del feature.)*

## Contextos acotados (DDD)

| Bounded Context | Responsabilidad | Entidades núcleo |
|---|---|---|
| Ingesta Cambiaria | Obtener, validar y cargar jornadas de tasas de referencia | Ingesta, Jornada, Tasa, Moneda |
| Consulta Cambiaria | Publicar y servir consultas de solo lectura sobre la serie ya cargada (FX-ING-002) | Publicación (JSON derivado), Consulta puntual, Serie, Clave API |

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

## Distribución y consulta en el edge (FX-ING-002)

Vista del bounded context Consulta Cambiaria: el pipeline precalcula la publicación como JSON derivado de SQLite (ADR-0007) y el Worker la sirve autenticada por clave API, con rate limiting en la plataforma (ADR-0008). El Worker no ejecuta ningún motor de consulta.

```mermaid
C4Container
    title Diagrama de contenedores — Distribucion y consulta (FX-ING-002)

    Person(analista, "Analista consumidor", "Consulta y descarga con su clave API")
    System_Ext(pipeline, "Pipeline de ingesta", "CronJob K8s: bcv-ingest (descargar + exportar) y rclone publica a R2", $tags="external")

    System_Boundary(edge, "Cloudflare edge") {
        Container(ui, "Web UI", "HTML/JS estatico en el Worker", "Formulario, tabla y descarga JSON; pide la clave al usuario, nunca la incrusta")
        Container(guard, "Guard de autenticacion", "Worker JS", "Default-deny sobre /api/*; clave en header X-Api-Key, comparacion en tiempo constante", $tags="owasp-a01")
        Container(api, "API de consulta", "Worker JS", "Valida parametros (allowlist), mapea a objetos de publicacion, filtra y pagina con topes", $tags="owasp-a03")
        ContainerDb(r2, "R2 bcv-fx-artefactos", "Objetos", "bcv_fx.db + publicacion/ (ultima, jornadas, series, monedas, indice)")
    }

    Rel(analista, ui, "Abre el formulario", "HTTPS")
    Rel(ui, api, "fetch de consultas", "HTTPS + X-Api-Key")
    Rel(guard, api, "Delega tras autenticar", "en proceso")
    Rel(api, r2, "Lee publicacion/", "binding R2")
    Rel(pipeline, r2, "Publica .db + publicacion/ en la misma corrida", "rclone")

    UpdateElementStyle(api, $bgColor="#1168bd", $fontColor="#ffffff")
    UpdateElementStyle(pipeline, $bgColor="#999999", $fontColor="#ffffff")
    UpdateElementStyle(guard, $borderColor="#b30000")
    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

### Flujo crítico de consulta

```mermaid
sequenceDiagram
    autonumber
    actor A as Analista
    participant UI as Web UI
    participant G as Guard de autenticacion
    participant API as API de consulta
    participant R2 as R2 publicacion/
    A->>UI: abre el formulario y aporta su clave API
    UI->>G: GET /api/tasas?fecha=2024-05-15&moneda=EUR (X-Api-Key)
    G->>G: validar clave (tiempo constante, default-deny)
    alt clave ausente o invalida
        G-->>UI: 401/403 (rechazo auditado con id de clave)
    else clave valida
        G->>API: request autenticado (id de clave para auditoria)
        API->>API: validar parametros (fecha ISO-8601, moneda en allowlist, topes)
        alt parametros invalidos
            API-->>UI: 400 controlado (sin detalles internos)
        else
            API->>R2: GET publicacion/jornadas/2024-05-15.json
            alt objeto inexistente (sin jornada)
                R2-->>API: null
                API-->>UI: 404 controlado (fecha sin jornada)
            else
                R2-->>API: JSON de la jornada
                API-->>UI: 200 + metadatos de frescura (sha256, generado_en)
            end
        end
    end
    UI-->>A: tabla de resultados y boton de descarga JSON
```

### Contrato de publicación (R2, prefijo `publicacion/`)

Derivado íntegramente de SQLite por `bcv-ingest exportar` (nuevo caso de uso `ExportarPublicacion` + puerto `ExportadorPublicacionPort`, mismo patrón hexagonal): `ultima.json`, `jornadas/AAAA-MM-DD.json`, `series/{MONEDA}.json`, `monedas.json` e `indice.json` (fechas disponibles, `sha256` del `.db`, `generado_en`). La cuarentena nunca se exporta. Detalle y alternativas en ADR-0007.

### Contrato de la API de consulta

El contrato de red del feature es el esqueleto OpenAPI en `docs/02-design/contracts/openapi-consulta.yaml` (endpoints `/api/tasas`, `/api/jornadas/ultima`, `/api/monedas`; seguridad `X-Api-Key`; errores 400/401/404/429 con shape uniforme). `/estado` y `/bcv_fx.db` conservan su contrato actual (RF16) y quedan fuera del OpenAPI.

## Contratos (CLI + schema SQLite)

No hay API de red en el bounded context de la ingesta: su contrato público es la CLI y el schema de la base. *(Actualización 2026-07-14: la API de red del bounded context Consulta Cambiaria se especifica en §Distribución y consulta y en `contracts/openapi-consulta.yaml` — FX-ING-002.)*

| Comando | Argumentos | Salida / exit code |
|---|---|---|
| `bcv-ingest descargar` | `--desde AAAA-MM --hasta AAAA-MM [--destino DIR]` | Resumen JSON por archivo; 0 OK, 2 cuarentenas, 3 error de red |
| `bcv-ingest cargar` | `RUTA` (archivo `.xls` o carpeta) | Resumen JSON: cargadas/duplicadas/cuarentena; 0 OK, 2 cuarentenas |
| `bcv-ingest estado` | `[--jornada AAAA-MM-DD]` | Estado de ingestas y cuarentenas pendientes; 0 siempre |
| `bcv-ingest exportar` | `--destino DIR` (propuesto, FX-ING-002) | Publicación JSON derivada de la base (`publicacion/`); 0 OK |

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
| T2 Suplantación de fuente | HTTPS con verificación estricta y fallo cerrado — sin flag de excepción (ADR-0004); hash SHA-256 registrado; respaldo: modo local | A02 |
| T4 Re-ingesta duplicada/alterada | Idempotencia por constraints (UNIQUE sha256, UNIQUE jornada+moneda) | A08 |
| T5 XLS malicioso | xlrd sin macros; límites de tamaño/filas; ingesta en proceso sin privilegios | A03/A08 |
| T6 Inyección SQL | Solo queries parametrizadas (sqlite3 placeholders) | A03 |
| T7 Mezcla de escalas | Campo `escala_monetaria` por jornada + tabla de vigencia de redenominaciones | A08 |
| T9 Clave API robada/filtrada | Secret en Wrangler, clave solo en header, rotación/revocación documentada (RS07) + auditoría por id de clave (RS11) | A01/A02 |
| T10 Inyección por parámetros de consulta | Validación allowlist (fecha ISO, moneda del catálogo) y mapeo cerrado parámetro→clave de objeto R2 — sin motor SQL en el edge (ADR-0007) | A03 |
| T11 Scraping masivo / DoS del servicio de consulta | Rate limiting de plataforma sobre `/api/*` + topes de página/respuesta en el Worker (ADR-0008) | A04 |
| T12 Bypass de autenticación (default-allow) | Guard default-deny: toda ruta `/api/*` nace protegida; comparación en tiempo constante (RS06) | A01 |
| T13 Enumeración de rutas / errores verbosos | Errores uniformes 400/404 sin detalles internos; 404 genérico fuera del contrato | A05 |
| T14 Caché compartida con respuestas autenticadas o publicación inconsistente | `cache-control` explícito por endpoint, cache key sin credenciales (RS10); publicación conjunta `.db` + `publicacion/` con `sha256` común en `indice.json` (ADR-0007) | A05/A08 |
| T15 Uso sin trazabilidad por clave | Log de acceso y de rechazo con identificador de clave, nunca la clave (RS11) | A09 |
