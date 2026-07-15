/**
 * Contrato del Worker (FX-ING-002): RF16 (rutas de distribución intactas) +
 * API de consulta autenticada según docs/02-design/contracts/openapi-consulta.yaml.
 * Corre en workerd real vía @cloudflare/vitest-pool-workers (miniflare R2).
 */
import { env, SELF } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";

const CLAVE = "clave-secreta-de-prueba"; // definida en vitest.config.js
const BASE = "https://worker.test";

const INDICE = {
  generado_en: "2026-07-14T21:00:00+00:00",
  sha256: "d".repeat(64),
  fechas: ["2024-05-14", "2024-05-15"],
  totales: { jornadas: 2, tasas: 3, monedas: 2 },
};

const JORNADA_15 = {
  fecha_operacion: "2024-05-15",
  fecha_valor: "2024-05-16",
  publicado_en: "2024-05-15 15:00:00",
  escala_monetaria: 1,
  tasas: [
    { moneda: "EUR", usd_bid: 1.1, usd_ask: 1.2, bs_bid: 40.0, bs_ask: 40.5, cotizacion_invertida: true },
    { moneda: "USD", usd_bid: 1.0, usd_ask: 1.0, bs_bid: 36.0, bs_ask: 36.4, cotizacion_invertida: false },
  ],
};

const SERIE_EUR = {
  moneda: "EUR",
  filas: [
    { fecha_operacion: "2024-05-13", fecha_valor: "2024-05-14", publicado_en: null, escala_monetaria: 1, usd_bid: 1.0, usd_ask: 1.1, bs_bid: 39.0, bs_ask: 39.5, cotizacion_invertida: true },
    { fecha_operacion: "2024-05-14", fecha_valor: "2024-05-15", publicado_en: null, escala_monetaria: 1, usd_bid: 1.05, usd_ask: 1.15, bs_bid: 39.5, bs_ask: 40.0, cotizacion_invertida: true },
    { fecha_operacion: "2024-05-15", fecha_valor: "2024-05-16", publicado_en: null, escala_monetaria: 1, usd_bid: 1.1, usd_ask: 1.2, bs_bid: 40.0, bs_ask: 40.5, cotizacion_invertida: true },
  ],
};

const MONEDAS = {
  monedas: [
    { codigo: "EUR", pais: "Zona Euro", es_iso4217: true, cotizacion_invertida: true },
    { codigo: "USD", pais: "Estados Unidos", es_iso4217: true, cotizacion_invertida: false },
  ],
};

beforeEach(async () => {
  await env.BUCKET.put("bcv_fx.db", "sqlite-de-mentira", {
    customMetadata: { sha256: "d".repeat(64) },
  });
  await env.BUCKET.put("publicacion/indice.json", JSON.stringify(INDICE));
  await env.BUCKET.put("publicacion/ultima.json", JSON.stringify(JORNADA_15));
  await env.BUCKET.put("publicacion/jornadas/2024-05-15.json", JSON.stringify(JORNADA_15));
  await env.BUCKET.put("publicacion/series/EUR.json", JSON.stringify(SERIE_EUR));
  await env.BUCKET.put("publicacion/monedas.json", JSON.stringify(MONEDAS));
});

function conClave(ruta, extra = {}) {
  return SELF.fetch(`${BASE}${ruta}`, { headers: { "x-api-key": CLAVE }, ...extra });
}

describe("RF16: distribución intacta (health.yml y consumidores actuales)", () => {
  it("GET /estado responde el shape exacto sin autenticación", async () => {
    const respuesta = await SELF.fetch(`${BASE}/estado`);
    expect(respuesta.status).toBe(200);
    const cuerpo = await respuesta.json();
    expect(Object.keys(cuerpo).sort()).toEqual(["bytes", "etag", "publicado", "sha256", "subido"]);
    expect(cuerpo.publicado).toBe(true);
    expect(cuerpo.sha256).toBe("d".repeat(64));
    expect(respuesta.headers.get("cache-control")).toBe("public, max-age=300");
  });

  it("GET /bcv_fx.db sirve el artefacto como attachment sin autenticación", async () => {
    const respuesta = await SELF.fetch(`${BASE}/bcv_fx.db`);
    expect(respuesta.status).toBe(200);
    expect(respuesta.headers.get("content-type")).toBe("application/vnd.sqlite3");
    expect(respuesta.headers.get("content-disposition")).toContain("attachment");
    expect(respuesta.headers.get("etag")).toBeTruthy();
    expect(await respuesta.text()).toBe("sqlite-de-mentira");
  });

  it("GET /estado responde 404 {publicado:false} sin artefacto", async () => {
    await env.BUCKET.delete("bcv_fx.db");
    const respuesta = await SELF.fetch(`${BASE}/estado`);
    expect(respuesta.status).toBe(404);
    expect(await respuesta.json()).toEqual({ publicado: false });
  });

  it("los métodos no soportados responden 405", async () => {
    const respuesta = await SELF.fetch(`${BASE}/api/tasas`, { method: "POST" });
    expect(respuesta.status).toBe(405);
  });
});

describe("RS06/RS10: default-deny en toda la superficie /api/*", () => {
  const rutas = ["/api/tasas?fecha=2024-05-15", "/api/jornadas/ultima", "/api/monedas", "/api/inexistente"];

  it.each(rutas)("401 sin clave en %s", async (ruta) => {
    const respuesta = await SELF.fetch(`${BASE}${ruta}`);
    expect(respuesta.status).toBe(401);
    expect(await respuesta.json()).toEqual({ error: "no autenticado" });
    expect(respuesta.headers.get("cache-control")).toBe("no-store");
  });

  it.each(rutas)("401 con clave inválida en %s", async (ruta) => {
    const respuesta = await SELF.fetch(`${BASE}${ruta}`, {
      headers: { "x-api-key": "clave-equivocada" },
    });
    expect(respuesta.status).toBe(401);
  });

  it("404 {error} en ruta /api/* desconocida aun autenticado", async () => {
    const respuesta = await conClave("/api/inexistente");
    expect(respuesta.status).toBe(404);
    expect(await respuesta.json()).toEqual({ error: "ruta no encontrada" });
  });

  it("la clave jamás viaja en la URL: query api_key no autentica", async () => {
    const respuesta = await SELF.fetch(`${BASE}/api/monedas?api_key=${CLAVE}`);
    expect(respuesta.status).toBe(401);
  });
});

describe("RF11/RF12: última jornada y catálogo", () => {
  it("GET /api/jornadas/ultima devuelve la jornada con metadatos de frescura (RF17)", async () => {
    const respuesta = await conClave("/api/jornadas/ultima");
    expect(respuesta.status).toBe(200);
    const cuerpo = await respuesta.json();
    expect(cuerpo.jornadas).toHaveLength(1);
    expect(cuerpo.jornadas[0].fecha_operacion).toBe("2024-05-15");
    expect(cuerpo.jornadas[0].tasas).toHaveLength(2);
    expect(cuerpo.publicacion).toEqual({ sha256: "d".repeat(64), generado_en: INDICE.generado_en });
    expect(respuesta.headers.get("cache-control")).toBe("no-store");
  });

  it("GET /api/monedas devuelve el catálogo publicado", async () => {
    const respuesta = await conClave("/api/monedas");
    const cuerpo = await respuesta.json();
    expect(cuerpo.monedas.map((m) => m.codigo)).toEqual(["EUR", "USD"]);
    expect(cuerpo.publicacion.sha256).toBe("d".repeat(64));
  });

  it("404 controlado si la publicación no existe todavía", async () => {
    await env.BUCKET.delete("publicacion/indice.json");
    const respuesta = await conClave("/api/jornadas/ultima");
    expect(respuesta.status).toBe(404);
    expect(await respuesta.json()).toEqual({ error: "publicación no disponible" });
  });
});

describe("RF09: consulta puntual por fecha", () => {
  it("devuelve la jornada completa", async () => {
    const respuesta = await conClave("/api/tasas?fecha=2024-05-15");
    expect(respuesta.status).toBe(200);
    const cuerpo = await respuesta.json();
    expect(cuerpo.jornadas[0].tasas).toHaveLength(2);
    expect(cuerpo.publicacion.generado_en).toBe(INDICE.generado_en);
  });

  it("filtra por moneda", async () => {
    const respuesta = await conClave("/api/tasas?fecha=2024-05-15&moneda=EUR");
    const cuerpo = await respuesta.json();
    expect(cuerpo.jornadas[0].tasas).toEqual([JORNADA_15.tasas[0]]);
  });

  it("404 controlado en fecha sin jornada (E5: feriado)", async () => {
    const respuesta = await conClave("/api/tasas?fecha=2024-05-12");
    expect(respuesta.status).toBe(404);
    expect(await respuesta.json()).toEqual({ error: "sin jornada para esa fecha" });
  });

  it("404 si la moneda no está en la jornada", async () => {
    const respuesta = await conClave("/api/tasas?fecha=2024-05-15&moneda=CHF");
    expect(respuesta.status).toBe(404);
  });
});

describe("RF10/RNF07: serie por rango con paginación", () => {
  it("devuelve el rango en orden cronológico con paginación", async () => {
    const respuesta = await conClave("/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR");
    const cuerpo = await respuesta.json();
    expect(cuerpo.jornadas.map((j) => j.fecha_operacion)).toEqual([
      "2024-05-13", "2024-05-14", "2024-05-15",
    ]);
    expect(cuerpo.jornadas[0].tasas[0].moneda).toBe("EUR");
    expect(cuerpo.paginacion).toEqual({ pagina: 1, limite: 1000, total_filas: 3 });
  });

  it("respeta pagina y limite (total_filas del rango completo)", async () => {
    const respuesta = await conClave(
      "/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR&pagina=2&limite=1",
    );
    const cuerpo = await respuesta.json();
    expect(cuerpo.jornadas.map((j) => j.fecha_operacion)).toEqual(["2024-05-14"]);
    expect(cuerpo.paginacion).toEqual({ pagina: 2, limite: 1, total_filas: 3 });
  });

  it("el rango recorta a las fechas disponibles", async () => {
    const respuesta = await conClave("/api/tasas?desde=2024-05-15&hasta=2024-06-30&moneda=EUR");
    const cuerpo = await respuesta.json();
    expect(cuerpo.paginacion.total_filas).toBe(1);
  });

  it("404 si la moneda no tiene serie", async () => {
    const respuesta = await conClave("/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=CHF");
    expect(respuesta.status).toBe(404);
  });
});

describe("RS08: validación estricta de parámetros (400 sin detalles internos)", () => {
  const casos = [
    "/api/tasas",                                                    // sin fecha ni rango
    "/api/tasas?fecha=15/05/2024",                                   // formato no ISO
    "/api/tasas?fecha=2024-13-99",                                   // fecha imposible
    "/api/tasas?fecha=2024-05-15&desde=2024-05-13&hasta=2024-05-15", // fecha y rango juntos
    "/api/tasas?desde=2024-05-13&hasta=2024-05-15",                  // rango sin moneda
    "/api/tasas?desde=2024-05-13&moneda=EUR",                        // rango incompleto
    "/api/tasas?desde=2024-05-15&hasta=2024-05-13&moneda=EUR",       // desde > hasta
    "/api/tasas?fecha=2024-05-15&moneda=usd",                        // minúsculas
    "/api/tasas?fecha=2024-05-15&moneda=EURO",                       // 4 letras
    "/api/tasas?fecha=2024-05-15&moneda=EUR'--",                     // payload
    "/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR&limite=0",
    "/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR&limite=1001",
    "/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR&pagina=0",
    "/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR&pagina=-1",
    "/api/tasas?fecha=2024-05-15&descarga=si",
  ];

  it.each(casos)("400 en %s", async (ruta) => {
    const respuesta = await conClave(ruta);
    expect(respuesta.status).toBe(400);
    const cuerpo = await respuesta.json();
    expect(Object.keys(cuerpo)).toEqual(["error"]);
    expect(cuerpo.error).not.toMatch(/stack|Error:|at /);
  });
});

describe("RF13: descarga del resultado como archivo JSON", () => {
  it("descarga=true añade content-disposition con el mismo shape", async () => {
    const normal = await conClave("/api/tasas?fecha=2024-05-15");
    const descarga = await conClave("/api/tasas?fecha=2024-05-15&descarga=true");
    expect(descarga.status).toBe(200);
    expect(descarga.headers.get("content-disposition")).toBe(
      'attachment; filename="tasas_2024-05-15.json"',
    );
    expect(await descarga.json()).toEqual(await normal.json());
  });

  it("en rango el filename lleva moneda y fechas", async () => {
    const respuesta = await conClave(
      "/api/tasas?desde=2024-05-13&hasta=2024-05-15&moneda=EUR&descarga=true",
    );
    expect(respuesta.headers.get("content-disposition")).toBe(
      'attachment; filename="tasas_EUR_2024-05-13_2024-05-15.json"',
    );
  });
});

describe("Web UI (RF14/RS10)", () => {
  it("GET / sirve la UI con CSP estricta y nosniff, sin autenticación", async () => {
    const respuesta = await SELF.fetch(`${BASE}/`);
    expect(respuesta.status).toBe(200);
    expect(respuesta.headers.get("content-type")).toContain("text/html");
    const csp = respuesta.headers.get("content-security-policy");
    expect(csp).toContain("default-src 'none'");
    expect(csp).toContain("connect-src 'self'");
    expect(respuesta.headers.get("x-content-type-options")).toBe("nosniff");
    const html = await respuesta.text();
    expect(html).toContain("X-Api-Key");
    expect(html).not.toContain(CLAVE); // la clave jamás incrustada (RF15)
  });
});
