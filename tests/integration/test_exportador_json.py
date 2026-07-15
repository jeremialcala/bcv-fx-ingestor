"""Integración del ExportadorJsonLocal: archivos reales bajo publicacion/ en UTF-8."""
import json

import pytest

from bcv_ingest.adaptadores.exportador_json import ExportadorJsonLocal


def test_escribe_bajo_publicacion_con_subcarpetas(tmp_path):
    exportador = ExportadorJsonLocal(tmp_path)
    exportador.escribir("jornadas/2024-05-15.json", {"fecha_operacion": "2024-05-15"})

    ruta = tmp_path / "publicacion" / "jornadas" / "2024-05-15.json"
    assert ruta.is_file()
    assert json.loads(ruta.read_text(encoding="utf-8")) == {"fecha_operacion": "2024-05-15"}


def test_contenido_utf8_sin_escapes(tmp_path):
    # en Windows, sin encoding explícito esto se escribiría en cp1252 (riesgo del plan)
    exportador = ExportadorJsonLocal(tmp_path)
    exportador.escribir("monedas.json", {"monedas": [{"codigo": "TRY", "pais": "Turquía"}]})

    crudo = (tmp_path / "publicacion" / "monedas.json").read_text(encoding="utf-8")
    assert "Turquía" in crudo  # ensure_ascii=False: legible, no í


@pytest.mark.parametrize("ruta", ["../fuera.json", "/absoluta.json", "series/../../fuera.json"])
def test_rechaza_rutas_fuera_del_prefijo(tmp_path, ruta):
    exportador = ExportadorJsonLocal(tmp_path)
    with pytest.raises(ValueError):
        exportador.escribir(ruta, {})
