# Imagen del ingestor BCV FX. Multi-stage: el builder instala el paquete y el runtime
# corre como usuario sin privilegios (RS02/T5: el XLS es entrada no confiable).
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/jeremialcala/bcv-fx-ingestor" \
      org.opencontainers.image.description="Ingesta idempotente de los tipos de cambio de referencia históricos del BCV hacia SQLite" \
      org.opencontainers.image.licenses="MIT"

COPY --from=builder /install /usr/local

# El portal BCV envía una cadena TLS incompleta; OpenSSL no hace AIA fetching, así que
# se añade el intermedio público de Sectigo al almacén (ver deploy/docker/ca-extra/README.md).
# La verificación sigue siendo estricta: la cadena debe terminar en una raíz de confianza.
COPY deploy/docker/ca-extra/*.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates \
    && python -m pip install --no-cache-dir --upgrade pip \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin ingestor \
    && mkdir /data && chown 10001:10001 /data

USER 10001
WORKDIR /data
VOLUME ["/data"]

ENTRYPOINT ["bcv-ingest"]
CMD ["--help"]
