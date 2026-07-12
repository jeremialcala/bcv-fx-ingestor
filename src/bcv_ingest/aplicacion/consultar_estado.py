"""Caso de uso: estado de ingestas y cuarentenas pendientes (RF08)."""
from __future__ import annotations

from datetime import date

from ..dominio.puertos import RepositorioTasasPort


class ConsultarEstadoUseCase:
    def __init__(self, repositorio: RepositorioTasasPort) -> None:
        self._repositorio = repositorio

    def ejecutar(self, fecha_operacion: date | None = None) -> dict:
        return self._repositorio.estado_general(fecha_operacion)
