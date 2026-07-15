"""Unit del caso de uso ExportarPublicacion (ADR-0007): shapes y pivote de series."""
from bcv_ingest.aplicacion.exportar_publicacion import ExportarPublicacionUseCase


class FakeExportador:
    def __init__(self):
        self.documentos: dict[str, dict] = {}

    def escribir(self, ruta_relativa: str, datos: dict) -> None:
        self.documentos[ruta_relativa] = datos


class FakeRepositorio:
    def __init__(self, jornadas=(), monedas=()):
        self._jornadas = list(jornadas)
        self._monedas = list(monedas)

    def jornadas_publicables(self):
        yield from self._jornadas

    def monedas_publicables(self):
        return list(self._monedas)


def _jornada(fecha, tasas):
    return {
        "fecha_operacion": fecha,
        "fecha_valor": fecha,
        "publicado_en": f"{fecha} 15:00:00",
        "escala_monetaria": 1,
        "tasas": tasas,
    }


def _tasa(moneda, invertida=False):
    return {
        "moneda": moneda,
        "usd_bid": 1.0,
        "usd_ask": 2.0,
        "bs_bid": 3.0,
        "bs_ask": 4.0,
        "cotizacion_invertida": invertida,
    }


MONEDAS = [
    {"codigo": "EUR", "pais": "Zona Euro", "es_iso4217": True, "cotizacion_invertida": True},
    {"codigo": "USD", "pais": "EEUU", "es_iso4217": True, "cotizacion_invertida": False},
]


def test_exporta_los_cinco_tipos_de_documento():
    exportador = FakeExportador()
    repo = FakeRepositorio(
        jornadas=[
            _jornada("2024-05-14", [_tasa("USD")]),
            _jornada("2024-05-15", [_tasa("EUR", True), _tasa("USD")]),
        ],
        monedas=MONEDAS,
    )
    resumen = ExportarPublicacionUseCase(repo, exportador).ejecutar("f" * 64)

    docs = exportador.documentos
    assert set(docs) == {
        "jornadas/2024-05-14.json",
        "jornadas/2024-05-15.json",
        "ultima.json",
        "series/EUR.json",
        "series/USD.json",
        "monedas.json",
        "indice.json",
    }
    assert resumen == {
        "jornadas": 2,
        "series": 2,
        "monedas": 2,
        "generado_en": docs["indice.json"]["generado_en"],
    }


def test_ultima_es_la_jornada_de_fecha_maxima():
    exportador = FakeExportador()
    repo = FakeRepositorio(
        jornadas=[
            _jornada("2024-05-14", [_tasa("USD")]),
            _jornada("2024-05-15", [_tasa("EUR", True)]),
        ],
        monedas=MONEDAS,
    )
    ExportarPublicacionUseCase(repo, exportador).ejecutar("f" * 64)

    ultima = exportador.documentos["ultima.json"]
    assert ultima["fecha_operacion"] == "2024-05-15"
    assert ultima == exportador.documentos["jornadas/2024-05-15.json"]


def test_series_pivotan_por_moneda_en_orden_cronologico():
    exportador = FakeExportador()
    repo = FakeRepositorio(
        jornadas=[
            _jornada("2024-05-14", [_tasa("USD")]),
            _jornada("2024-05-15", [_tasa("USD")]),
        ],
        monedas=MONEDAS[1:],
    )
    ExportarPublicacionUseCase(repo, exportador).ejecutar("f" * 64)

    serie = exportador.documentos["series/USD.json"]
    assert serie["moneda"] == "USD"
    assert [f["fecha_operacion"] for f in serie["filas"]] == ["2024-05-14", "2024-05-15"]
    fila = serie["filas"][0]
    assert fila["usd_bid"] == 1.0 and fila["bs_ask"] == 4.0
    assert fila["escala_monetaria"] == 1
    assert fila["cotizacion_invertida"] is False


def test_indice_referencia_sha256_fechas_y_totales():
    exportador = FakeExportador()
    repo = FakeRepositorio(
        jornadas=[_jornada("2024-05-15", [_tasa("EUR", True), _tasa("USD")])],
        monedas=MONEDAS,
    )
    ExportarPublicacionUseCase(repo, exportador).ejecutar("abc123" + "0" * 58)

    indice = exportador.documentos["indice.json"]
    assert indice["sha256"] == "abc123" + "0" * 58
    assert indice["fechas"] == ["2024-05-15"]
    assert indice["totales"] == {"jornadas": 1, "tasas": 2, "monedas": 2}
    assert indice["generado_en"].endswith("+00:00")  # UTC explícito


def test_base_vacia_exporta_solo_monedas_e_indice():
    exportador = FakeExportador()
    repo = FakeRepositorio(jornadas=[], monedas=[])
    resumen = ExportarPublicacionUseCase(repo, exportador).ejecutar("f" * 64)

    assert set(exportador.documentos) == {"monedas.json", "indice.json"}
    assert exportador.documentos["indice.json"]["fechas"] == []
    assert resumen["jornadas"] == 0 and resumen["series"] == 0
