"""Entidades y objetos de valor del dominio (lenguaje ubicuo del glosario)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path


class ErrorIngesta(Exception):
    """Error base del dominio de ingesta."""


class ArchivoIlegibleError(ErrorIngesta):
    """El archivo no puede tratarse como un XLS SMC (corrupto, excede límites, formato ajeno)."""


class ErrorDescarga(ErrorIngesta):
    """Fallo de red o TLS al descargar del portal BCV (exit code 3 en la CLI)."""


class EstadoIngesta(str, Enum):
    DETECTADO = "detectado"
    OBTENIDO = "obtenido"
    DUPLICADO = "duplicado"
    VALIDANDO = "validando"
    CARGADO = "cargado"
    CARGADO_PARCIAL = "cargado_parcial"
    CUARENTENA = "cuarentena"
    FALLIDO = "fallido"


class OrigenArchivo(str, Enum):
    DESCARGA = "descarga"
    LOCAL = "local"


@dataclass(frozen=True)
class ArchivoSmc:
    ruta: Path
    sha256: str
    origen: OrigenArchivo

    @property
    def nombre(self) -> str:
        return self.ruta.name


@dataclass(frozen=True)
class TasaCruda:
    """Fila de moneda tal como sale de la hoja, sin validar. None = celda vacía o no numérica."""

    codigo_moneda: str
    pais: str
    usd_bid: float | None
    usd_ask: float | None
    bs_bid: float | None
    bs_ask: float | None
    fila: int


@dataclass(frozen=True)
class JornadaCruda:
    hoja: str
    fecha_operacion: date
    fecha_valor: date
    publicado_en: datetime | None
    tasas: tuple[TasaCruda, ...]


@dataclass(frozen=True)
class TasaValidada:
    codigo_moneda: str
    usd_bid: float
    usd_ask: float
    bs_bid: float
    bs_ask: float
    cotizacion_invertida: bool


@dataclass(frozen=True)
class JornadaValidada:
    fecha_operacion: date
    fecha_valor: date
    publicado_en: datetime | None
    escala_monetaria: int
    tasas: tuple[TasaValidada, ...]


@dataclass(frozen=True)
class ItemCuarentena:
    hoja: str | None
    motivo: str
    payload_crudo: str | None = None


@dataclass(frozen=True)
class ResultadoCarga:
    jornada_nueva: bool
    tasas_nuevas: int
    tasas_duplicadas: int


@dataclass
class ResumenIngesta:
    archivo: str
    sha256: str
    origen: str
    estado: str
    jornadas_cargadas: int = 0
    tasas_cargadas: int = 0
    duplicadas: int = 0
    cuarentenas: list[ItemCuarentena] = field(default_factory=list)

    def como_dict(self) -> dict:
        return {
            "archivo": self.archivo,
            "sha256": self.sha256,
            "origen": self.origen,
            "estado": self.estado,
            "jornadas_cargadas": self.jornadas_cargadas,
            "tasas_cargadas": self.tasas_cargadas,
            "duplicadas": self.duplicadas,
            "cuarentenas": [
                {"hoja": c.hoja, "motivo": c.motivo} for c in self.cuarentenas
            ],
        }


_PATRON_MES = re.compile(r"^(\d{4})-(\d{2})$")
_LETRAS_TRIMESTRE = "abcd"


@dataclass(frozen=True, order=True)
class Periodo:
    """Trimestre de publicación de un Archivo SMC (glosario: `2_1_2{t}{AA}_smc.xls`)."""

    anio: int
    trimestre: int

    def __post_init__(self) -> None:
        if not 1 <= self.trimestre <= 4:
            raise ValueError(f"trimestre fuera de rango: {self.trimestre}")

    @property
    def letra(self) -> str:
        return _LETRAS_TRIMESTRE[self.trimestre - 1]

    @property
    def nombre_archivo(self) -> str:
        return f"2_1_2{self.letra}{self.anio % 100:02d}_smc.xls"

    def __str__(self) -> str:
        return f"{self.anio}-T{'I' * self.trimestre if self.trimestre < 4 else 'IV'}"

    @classmethod
    def desde_mes(cls, texto: str) -> "Periodo":
        m = _PATRON_MES.match(texto.strip())
        if not m:
            raise ValueError(f"mes inválido, se espera AAAA-MM: {texto!r}")
        anio, mes = int(m.group(1)), int(m.group(2))
        if not 1 <= mes <= 12:
            raise ValueError(f"mes fuera de rango: {texto!r}")
        return cls(anio, (mes - 1) // 3 + 1)

    @staticmethod
    def rango(desde: "Periodo", hasta: "Periodo") -> list["Periodo"]:
        if desde > hasta:
            raise ValueError(f"rango invertido: {desde} > {hasta}")
        periodos = []
        actual = desde
        while actual <= hasta:
            periodos.append(actual)
            if actual.trimestre == 4:
                actual = Periodo(actual.anio + 1, 1)
            else:
                actual = Periodo(actual.anio, actual.trimestre + 1)
        return periodos
