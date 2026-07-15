"""Puertos del núcleo (Clean Architecture): los adaptadores los implementan."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

from .modelos import (
    ArchivoSmc,
    EstadoIngesta,
    ItemCuarentena,
    JornadaCruda,
    JornadaValidada,
    Periodo,
    ResultadoCarga,
)


@dataclass(frozen=True)
class ResultadoParseo:
    jornadas: tuple[JornadaCruda, ...]
    descartes: tuple[ItemCuarentena, ...]


class FuenteArchivosPort(ABC):
    """Origen de archivos SMC (ADR-0002): descarga del portal o carpeta local."""

    @abstractmethod
    def obtener(self, periodo: Periodo | None = None) -> Iterator[ArchivoSmc]:
        """Produce 0..n archivos; el descargador exige `periodo`, la carpeta lo ignora."""


class LectorTasasPort(ABC):
    @abstractmethod
    def parsear(self, archivo: ArchivoSmc) -> ResultadoParseo:
        """Parsea las hojas DDMMYYYY. Lanza ArchivoIlegibleError si el archivo entero es inválido."""


class RepositorioTasasPort(ABC):
    @abstractmethod
    def hash_conocido(self, sha256: str) -> bool:
        """True si el hash corresponde a una ingesta ya cargada (total o parcial)."""

    @abstractmethod
    def nombre_archivo_ingerido(self, nombre: str) -> bool:
        """True si un archivo con ese nombre ya fue cargado (RF01: no re-descargar)."""

    @abstractmethod
    def registrar_ingesta(self, archivo: ArchivoSmc, estado: EstadoIngesta) -> int: ...

    @abstractmethod
    def actualizar_estado(self, ingesta_id: int, estado: EstadoIngesta) -> None: ...

    @abstractmethod
    def guardar_jornada(self, jornada: JornadaValidada, ingesta_id: int) -> ResultadoCarga: ...

    @abstractmethod
    def enviar_a_cuarentena(self, ingesta_id: int, item: ItemCuarentena) -> None: ...

    @abstractmethod
    def confirmar(self) -> None:
        """Confirma la transacción de la ingesta en curso (una por archivo)."""

    @abstractmethod
    def revertir(self) -> None: ...

    @abstractmethod
    def estado_general(self, fecha_operacion=None) -> dict: ...

    @abstractmethod
    def jornadas_publicables(self) -> Iterator[dict]:
        """Jornadas cargadas con sus tasas, en orden cronológico, con el shape
        Jornada de la publicación (ADR-0007). La cuarentena queda fuera por
        construcción: solo lee jornada/tasa/moneda."""

    @abstractmethod
    def monedas_publicables(self) -> list[dict]:
        """Catálogo de la publicación: solo monedas con al menos una tasa,
        con `cotizacion_invertida` tomada de la tabla tasa."""


class ExportadorPublicacionPort(ABC):
    """Destino de la publicación derivada (ADR-0007). El caso de uso arma los
    documentos; el adaptador solo los materializa bajo el prefijo publicacion/."""

    @abstractmethod
    def escribir(self, ruta_relativa: str, datos: dict) -> None:
        """Escribe un documento JSON en publicacion/<ruta_relativa> (UTF-8)."""
