"""CLI `bcv-ingest` — contrato público (architecture.md §Contratos).

Exit codes: 0 OK; 2 hubo cuarentenas; 3 error de red o TLS en descarga.
La salida de datos es JSON por stdout; los logs de auditoría van por stderr (RNF03).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from .adaptadores.carpeta_local import CarpetaLocalAdapter
from .adaptadores.descargador_http import DescargadorHttpBcv
from .adaptadores.lector_xls import LectorXlsXlrd
from .adaptadores.repositorio_sqlite import RepositorioSqlite
from .aplicacion.consultar_estado import ConsultarEstadoUseCase
from .aplicacion.descargar_periodo import DescargarPeriodoUseCase
from .aplicacion.ingestar_archivo import IngestarArchivoUseCase
from .dominio.modelos import ErrorDescarga, Periodo
from .dominio.validador import ValidadorDominio

EXIT_OK = 0
EXIT_CUARENTENAS = 2
EXIT_ERROR_RED = 3


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bcv-ingest",
        description="Ingesta de tipos de cambio de referencia históricos del BCV a SQLite",
    )
    parser.add_argument("--db", default="bcv_fx.db", help="ruta de la base SQLite (default: bcv_fx.db)")
    parser.add_argument("--verboso", action="store_true", help="logs de nivel DEBUG")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    descargar = subparsers.add_parser(
        "descargar", help="descarga archivos SMC del portal BCV por rango de meses e ingiere"
    )
    descargar.add_argument("--desde", required=True, metavar="AAAA-MM")
    descargar.add_argument("--hasta", required=True, metavar="AAAA-MM")
    descargar.add_argument("--destino", default="entrada", metavar="DIR",
                           help="carpeta donde guardar los XLS (default: entrada)")
    descargar.add_argument("--forzar", action="store_true",
                           help="re-descarga aunque el archivo ya esté ingerido "
                                "(útil para el trimestre en curso)")

    cargar = subparsers.add_parser("cargar", help="ingiere un archivo .xls o una carpeta local")
    cargar.add_argument("ruta", metavar="RUTA")

    estado = subparsers.add_parser("estado", help="estado de ingestas y cuarentenas pendientes")
    estado.add_argument("--jornada", metavar="AAAA-MM-DD")

    return parser


def main(argv: list[str] | None = None) -> int:
    # salida determinista en UTF-8 (en Windows los pipes heredan cp1252)
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    parser = construir_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verboso else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    repositorio = RepositorioSqlite(args.db)
    try:
        if args.comando == "cargar":
            return _cargar(args, repositorio, parser)
        if args.comando == "descargar":
            return _descargar(args, repositorio, parser)
        return _estado(args, repositorio, parser)
    finally:
        repositorio.cerrar()


def _ingestar_use_case(repositorio: RepositorioSqlite) -> IngestarArchivoUseCase:
    return IngestarArchivoUseCase(LectorXlsXlrd(), ValidadorDominio(), repositorio)


def _cargar(args, repositorio, parser) -> int:
    ruta = Path(args.ruta)
    if not ruta.exists():
        parser.error(f"la ruta no existe: {ruta}")
    ingestar = _ingestar_use_case(repositorio)
    fuente = CarpetaLocalAdapter(ruta)
    resumenes = [ingestar.ejecutar(archivo).como_dict() for archivo in fuente.obtener()]
    _imprimir(resumenes)
    hubo_cuarentenas = any(r["cuarentenas"] for r in resumenes)
    return EXIT_CUARENTENAS if hubo_cuarentenas else EXIT_OK


def _descargar(args, repositorio, parser) -> int:
    try:
        desde = Periodo.desde_mes(args.desde)
        hasta = Periodo.desde_mes(args.hasta)
    except ValueError as error:
        parser.error(str(error))
    caso = DescargarPeriodoUseCase(
        DescargadorHttpBcv(Path(args.destino)), _ingestar_use_case(repositorio), repositorio
    )
    try:
        resultados = caso.ejecutar(desde, hasta, forzar=args.forzar)
    except ErrorDescarga as error:
        _imprimir({"error": str(error)})
        return EXIT_ERROR_RED
    _imprimir(resultados)
    hubo_cuarentenas = any(r.get("cuarentenas") for r in resultados)
    return EXIT_CUARENTENAS if hubo_cuarentenas else EXIT_OK


def _estado(args, repositorio, parser) -> int:
    fecha = None
    if args.jornada:
        try:
            fecha = date.fromisoformat(args.jornada)
        except ValueError:
            parser.error(f"jornada inválida, se espera AAAA-MM-DD: {args.jornada!r}")
    _imprimir(ConsultarEstadoUseCase(repositorio).ejecutar(fecha))
    return EXIT_OK


def _imprimir(datos) -> None:
    print(json.dumps(datos, ensure_ascii=False, indent=2, default=str))


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
