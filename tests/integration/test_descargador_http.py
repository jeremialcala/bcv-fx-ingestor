import httpx
import pytest

from bcv_ingest.adaptadores.descargador_http import URL_BASE, DescargadorHttpBcv
from bcv_ingest.dominio.modelos import ErrorDescarga, OrigenArchivo, Periodo


def cliente_simulado(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_descarga_exitosa_guarda_y_hashea(tmp_path):
    contenido = b"bytes del xls (el parseo no es responsabilidad del descargador)"

    def handler(request):
        assert str(request.url) == URL_BASE + "2_1_2a20_smc.xls"
        return httpx.Response(200, content=contenido)

    descargador = DescargadorHttpBcv(tmp_path, cliente=cliente_simulado(handler))
    archivos = list(descargador.obtener(Periodo(2020, 1)))

    assert len(archivos) == 1
    assert archivos[0].origen == OrigenArchivo.DESCARGA
    assert archivos[0].ruta.read_bytes() == contenido
    assert len(archivos[0].sha256) == 64


def test_404_significa_periodo_no_publicado(tmp_path):
    descargador = DescargadorHttpBcv(
        tmp_path, cliente=cliente_simulado(lambda r: httpx.Response(404))
    )
    assert list(descargador.obtener(Periodo(2019, 1))) == []


def test_http_inesperado_es_error_de_descarga(tmp_path):
    descargador = DescargadorHttpBcv(
        tmp_path, cliente=cliente_simulado(lambda r: httpx.Response(503))
    )
    with pytest.raises(ErrorDescarga, match="HTTP 503"):
        list(descargador.obtener(Periodo(2020, 1)))


def test_fallo_de_transporte_reintenta_y_falla_cerrado(tmp_path):
    intentos = []

    def handler(request):
        intentos.append(1)
        raise httpx.ConnectError("certificate verify failed")  # p. ej. TLS inválido

    descargador = DescargadorHttpBcv(
        tmp_path, cliente=cliente_simulado(handler), reintentos=3, pausa_base=0
    )
    with pytest.raises(ErrorDescarga, match="fallo de red o TLS"):
        list(descargador.obtener(Periodo(2020, 1)))
    assert len(intentos) == 3  # backoff con reintentos (T8), sin degradar TLS (ADR-0004)


def test_sin_periodo_es_error_de_uso(tmp_path):
    with pytest.raises(ValueError):
        DescargadorHttpBcv(tmp_path).obtener(None)
