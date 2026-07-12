"""RepositorioSqlite: persistencia idempotente (ADR-0001, RS03, RS05).

El schema es el contrato definido en `docs/02-design/architecture.md` §Contratos.
La idempotencia la fuerzan los constraints (UNIQUE sha256, UNIQUE fecha_operacion,
UNIQUE jornada+moneda), no la lógica de aplicación. Todas las queries van
parametrizadas. Una transacción por archivo: `confirmar()`/`revertir()` las maneja
el caso de uso.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from ..dominio.modelos import (
    ArchivoSmc,
    EstadoIngesta,
    ItemCuarentena,
    JornadaValidada,
    ResultadoCarga,
)
from ..dominio.monedas import CATALOGO
from ..dominio.puertos import RepositorioTasasPort

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ingesta (
  id INTEGER PRIMARY KEY,
  nombre_archivo TEXT NOT NULL,
  sha256 TEXT NOT NULL UNIQUE,
  origen TEXT NOT NULL CHECK (origen IN ('descarga','local')),
  estado TEXT NOT NULL,
  procesado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS moneda (
  id INTEGER PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE,
  pais TEXT NOT NULL,
  es_iso4217 INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS jornada (
  id INTEGER PRIMARY KEY,
  fecha_operacion TEXT NOT NULL UNIQUE,
  fecha_valor TEXT NOT NULL,
  publicado_en TEXT,
  escala_monetaria INTEGER NOT NULL DEFAULT 1,
  ingesta_id INTEGER NOT NULL REFERENCES ingesta(id),
  CHECK (fecha_valor >= fecha_operacion)
);
CREATE TABLE IF NOT EXISTS tasa (
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
CREATE TABLE IF NOT EXISTS cuarentena (
  id INTEGER PRIMARY KEY,
  ingesta_id INTEGER NOT NULL REFERENCES ingesta(id),
  hoja TEXT,
  motivo TEXT NOT NULL,
  payload_crudo TEXT,
  creado_en TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_ESTADOS_INGERIDOS = (EstadoIngesta.CARGADO.value, EstadoIngesta.CARGADO_PARCIAL.value)

# solo SQL literal: nada de construir queries con strings (RS03)
_CONSULTAS_CONTEO = {
    "ingesta": "SELECT COUNT(*) AS n FROM ingesta",
    "jornada": "SELECT COUNT(*) AS n FROM jornada",
    "tasa": "SELECT COUNT(*) AS n FROM tasa",
    "cuarentena": "SELECT COUNT(*) AS n FROM cuarentena",
    "moneda": "SELECT COUNT(*) AS n FROM moneda",
}


class RepositorioSqlite(RepositorioTasasPort):
    def __init__(self, ruta_db: str | Path) -> None:
        self._conn = sqlite3.connect(str(ruta_db))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._sembrar_monedas()
        self._conn.commit()
        self._monedas: dict[str, int] = {
            fila["codigo"]: fila["id"]
            for fila in self._conn.execute("SELECT id, codigo FROM moneda")
        }

    def _sembrar_monedas(self) -> None:
        self._conn.executemany(
            "INSERT OR IGNORE INTO moneda (codigo, pais, es_iso4217) VALUES (?, ?, ?)",
            [(m.codigo, m.pais, int(m.es_iso4217)) for m in CATALOGO.values()],
        )

    def hash_conocido(self, sha256: str) -> bool:
        fila = self._conn.execute(
            "SELECT 1 FROM ingesta WHERE sha256 = ? AND estado IN (?, ?)",
            (sha256, *_ESTADOS_INGERIDOS),
        ).fetchone()
        return fila is not None

    def nombre_archivo_ingerido(self, nombre: str) -> bool:
        fila = self._conn.execute(
            "SELECT 1 FROM ingesta WHERE nombre_archivo = ? AND estado IN (?, ?)",
            (nombre, *_ESTADOS_INGERIDOS),
        ).fetchone()
        return fila is not None

    def registrar_ingesta(self, archivo: ArchivoSmc, estado: EstadoIngesta) -> int:
        # el reproceso de una ingesta en cuarentena/fallida reutiliza su fila
        # (UNIQUE sha256) y limpia sus items de cuarentena previos
        fila = self._conn.execute(
            """
            INSERT INTO ingesta (nombre_archivo, sha256, origen, estado)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (sha256) DO UPDATE SET
              nombre_archivo = excluded.nombre_archivo,
              origen = excluded.origen,
              estado = excluded.estado,
              procesado_en = datetime('now')
            RETURNING id
            """,
            (archivo.nombre, archivo.sha256, archivo.origen.value, estado.value),
        ).fetchone()
        ingesta_id = fila["id"]
        self._conn.execute("DELETE FROM cuarentena WHERE ingesta_id = ?", (ingesta_id,))
        return ingesta_id

    def actualizar_estado(self, ingesta_id: int, estado: EstadoIngesta) -> None:
        self._conn.execute(
            "UPDATE ingesta SET estado = ? WHERE id = ?", (estado.value, ingesta_id)
        )

    def guardar_jornada(self, jornada: JornadaValidada, ingesta_id: int) -> ResultadoCarga:
        fila = self._conn.execute(
            "SELECT id FROM jornada WHERE fecha_operacion = ?",
            (jornada.fecha_operacion.isoformat(),),
        ).fetchone()
        if fila:
            jornada_id, jornada_nueva = fila["id"], False
        else:
            fila = self._conn.execute(
                """
                INSERT INTO jornada
                  (fecha_operacion, fecha_valor, publicado_en, escala_monetaria, ingesta_id)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    jornada.fecha_operacion.isoformat(),
                    jornada.fecha_valor.isoformat(),
                    jornada.publicado_en.isoformat(sep=" ") if jornada.publicado_en else None,
                    jornada.escala_monetaria,
                    ingesta_id,
                ),
            ).fetchone()
            jornada_id, jornada_nueva = fila["id"], True

        nuevas = duplicadas = 0
        for tasa in jornada.tasas:
            cursor = self._conn.execute(
                """
                INSERT OR IGNORE INTO tasa
                  (jornada_id, moneda_id, usd_bid, usd_ask, bs_bid, bs_ask, cotizacion_invertida)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    jornada_id,
                    self._monedas[tasa.codigo_moneda],
                    tasa.usd_bid,
                    tasa.usd_ask,
                    tasa.bs_bid,
                    tasa.bs_ask,
                    int(tasa.cotizacion_invertida),
                ),
            )
            if cursor.rowcount:
                nuevas += 1
            else:
                duplicadas += 1
        return ResultadoCarga(
            jornada_nueva=jornada_nueva, tasas_nuevas=nuevas, tasas_duplicadas=duplicadas
        )

    def enviar_a_cuarentena(self, ingesta_id: int, item: ItemCuarentena) -> None:
        self._conn.execute(
            "INSERT INTO cuarentena (ingesta_id, hoja, motivo, payload_crudo) VALUES (?, ?, ?, ?)",
            (ingesta_id, item.hoja, item.motivo, item.payload_crudo),
        )

    def confirmar(self) -> None:
        self._conn.commit()

    def revertir(self) -> None:
        self._conn.rollback()

    def estado_general(self, fecha_operacion: date | None = None) -> dict:
        estado = {
            "ingestas": [
                dict(fila)
                for fila in self._conn.execute(
                    "SELECT nombre_archivo, sha256, origen, estado, procesado_en "
                    "FROM ingesta ORDER BY procesado_en DESC, id DESC"
                )
            ],
            "totales": {
                "jornadas": self._contar("jornada"),
                "tasas": self._contar("tasa"),
                "cuarentenas_pendientes": self._contar("cuarentena"),
            },
            "cuarentenas": [
                dict(fila)
                for fila in self._conn.execute(
                    """
                    SELECT c.hoja, c.motivo, c.creado_en, i.nombre_archivo AS archivo
                    FROM cuarentena c JOIN ingesta i ON i.id = c.ingesta_id
                    ORDER BY c.creado_en DESC, c.id DESC
                    """
                )
            ],
        }
        if fecha_operacion is not None:
            fila = self._conn.execute(
                """
                SELECT j.fecha_operacion, j.fecha_valor, j.publicado_en, j.escala_monetaria,
                       i.nombre_archivo AS archivo, COUNT(t.id) AS tasas
                FROM jornada j
                JOIN ingesta i ON i.id = j.ingesta_id
                LEFT JOIN tasa t ON t.jornada_id = j.id
                WHERE j.fecha_operacion = ?
                GROUP BY j.id
                """,
                (fecha_operacion.isoformat(),),
            ).fetchone()
            hoja = fecha_operacion.strftime("%d%m%Y")
            estado["jornada"] = dict(fila) if fila else None
            estado["cuarentenas"] = [
                c for c in estado["cuarentenas"] if c["hoja"] == hoja
            ]
        return estado

    def _contar(self, tabla: str) -> int:
        return self._conn.execute(_CONSULTAS_CONTEO[tabla]).fetchone()["n"]

    def cerrar(self) -> None:
        self._conn.close()
