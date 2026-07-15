"""Caso de uso: exportar la publicación JSON derivada de la base (RF09–RF13 vía ADR-0007).

Genera el prefijo `publicacion/` que el Worker sirve sin motor de consulta:
`ultima.json`, `jornadas/AAAA-MM-DD.json`, `series/{MONEDA}.json`, `monedas.json`
e `indice.json`. El índice se escribe al final para que nunca referencie objetos
aún no materializados. La cuarentena queda fuera por construcción (paridad con
el .db: solo lo cargado se publica).
"""
from __future__ import annotations

from datetime import datetime, timezone

from ..dominio.puertos import ExportadorPublicacionPort, RepositorioTasasPort


class ExportarPublicacionUseCase:
    def __init__(
        self, repositorio: RepositorioTasasPort, exportador: ExportadorPublicacionPort
    ) -> None:
        self._repositorio = repositorio
        self._exportador = exportador

    def ejecutar(self, sha256_db: str) -> dict:
        generado_en = datetime.now(timezone.utc).isoformat()
        fechas: list[str] = []
        series: dict[str, list[dict]] = {}
        ultima: dict | None = None
        total_tasas = 0

        for jornada in self._repositorio.jornadas_publicables():
            fecha = jornada["fecha_operacion"]
            fechas.append(fecha)
            total_tasas += len(jornada["tasas"])
            self._exportador.escribir(f"jornadas/{fecha}.json", jornada)
            ultima = jornada
            for tasa in jornada["tasas"]:
                series.setdefault(tasa["moneda"], []).append(
                    {
                        "fecha_operacion": fecha,
                        "fecha_valor": jornada["fecha_valor"],
                        "publicado_en": jornada["publicado_en"],
                        "escala_monetaria": jornada["escala_monetaria"],
                        "usd_bid": tasa["usd_bid"],
                        "usd_ask": tasa["usd_ask"],
                        "bs_bid": tasa["bs_bid"],
                        "bs_ask": tasa["bs_ask"],
                        "cotizacion_invertida": tasa["cotizacion_invertida"],
                    }
                )

        if ultima is not None:
            self._exportador.escribir("ultima.json", ultima)
        for moneda, filas in series.items():
            self._exportador.escribir(f"series/{moneda}.json", {"moneda": moneda, "filas": filas})

        monedas = self._repositorio.monedas_publicables()
        self._exportador.escribir("monedas.json", {"monedas": monedas})

        # el índice va al final: un indice.json publicado siempre referencia objetos ya escritos
        self._exportador.escribir(
            "indice.json",
            {
                "generado_en": generado_en,
                "sha256": sha256_db,
                "fechas": fechas,
                "totales": {
                    "jornadas": len(fechas),
                    "tasas": total_tasas,
                    "monedas": len(monedas),
                },
            },
        )
        return {
            "jornadas": len(fechas),
            "series": len(series),
            "monedas": len(monedas),
            "generado_en": generado_en,
        }
