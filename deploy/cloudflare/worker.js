/**
 * Worker de distribución y consulta del artefacto bcv_fx.db (edge-first).
 *
 * Distribución (ADR-0006) + consulta autenticada (FX-ING-002, ADR-0007 que la
 * supersede parcialmente): el CronJob de K8s publica en R2 el artefacto y la
 * publicación JSON precalculada (`publicacion/`); este Worker sirve ambos sin
 * ningún motor de consulta — cada endpoint es una lectura de objeto más, a lo
 * sumo, filtro y paginación en memoria. Rate limiting en la plataforma más
 * topes de página aquí (ADR-0008).
 *
 * Rutas:
 *   GET /bcv_fx.db            -> el archivo SQLite (attachment, ETag, caché 1 h)
 *   GET /estado               -> metadatos del artefacto publicado (JSON, público)
 *   GET /                     -> Web UI de consulta (pide la clave al usuario)
 *   GET /api/tasas            -> puntual (?fecha=) o serie (?desde=&hasta=&moneda=)
 *   GET /api/jornadas/ultima  -> última jornada publicada
 *   GET /api/monedas          -> catálogo de la publicación
 *
 * Toda la superficie /api/* exige el header X-Api-Key contra el secret
 * API_KEYS ("id1:clave1,id2:clave2") con default-deny y comparación en tiempo
 * constante (RS06); respuestas autenticadas con cache-control: no-store (RS10);
 * errores con shape {error} sin detalles internos (T13); auditoría por id de
 * clave, jamás la clave (RS11).
 */
import { PAGINA_HTML } from "./ui.js";

const OBJETO = "bcv_fx.db";
const LIMITE_MAX = 1000; // RNF07 / ADR-0008: tope duro de filas por página
const RE_FECHA = /^\d{4}-\d{2}-\d{2}$/;
const RE_MONEDA = /^[A-Z]{3}$/;
const RE_ENTERO = /^\d+$/;

export default {
  async fetch(request, env) {
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("método no soportado", { status: 405, headers: { allow: "GET, HEAD" } });
    }
    const url = new URL(request.url);

    if (url.pathname === "/bcv_fx.db") {
      const objeto = await env.BUCKET.get(OBJETO);
      if (objeto === null) {
        return new Response("artefacto no publicado todavía", { status: 404 });
      }
      const headers = new Headers();
      objeto.writeHttpMetadata(headers);
      headers.set("etag", objeto.httpEtag);
      headers.set("content-type", "application/vnd.sqlite3");
      headers.set("content-disposition", 'attachment; filename="bcv_fx.db"');
      headers.set("cache-control", "public, max-age=3600");
      return new Response(request.method === "HEAD" ? null : objeto.body, { headers });
    }

    if (url.pathname === "/estado") {
      const objeto = await env.BUCKET.head(OBJETO);
      if (objeto === null) {
        return Response.json({ publicado: false }, { status: 404 });
      }
      return Response.json(
        {
          publicado: true,
          bytes: objeto.size,
          subido: objeto.uploaded,
          etag: objeto.httpEtag,
          sha256: objeto.customMetadata?.sha256 ?? null,
        },
        { headers: { "cache-control": "public, max-age=300" } },
      );
    }

    if (url.pathname === "/") {
      return new Response(request.method === "HEAD" ? null : PAGINA_HTML, {
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "public, max-age=300",
          // ningún origen externo; 'unsafe-inline' es el costo de la UI self-contained (RS10)
          "content-security-policy":
            "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; " +
            "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
          "x-content-type-options": "nosniff",
          "referrer-policy": "no-referrer",
        },
      });
    }

    if (url.pathname.startsWith("/api/")) {
      try {
        return await manejarApi(request, env, url);
      } catch (error) {
        // jamás stacktraces al cliente (T13); el detalle queda en observabilidad
        console.log(JSON.stringify({ evento: "error_interno", ruta: url.pathname, detalle: String(error) }));
        return respuestaApi({ error: "error interno" }, 500);
      }
    }

    return new Response("rutas disponibles: /, /api/*, /bcv_fx.db, /estado", { status: 404 });
  },
};

function respuestaApi(cuerpo, status = 200, extra = {}) {
  const headers = {
    "cache-control": "no-store", // respuestas autenticadas nunca en caché compartida (RS10)
    "x-content-type-options": "nosniff",
    ...extra,
  };
  return Response.json(cuerpo, { status, headers });
}

/** Compara dos strings en tiempo constante: SHA-256 de ambos lados y
 * timingSafeEqual sobre los digests (siempre 32 bytes — timingSafeEqual
 * lanza con longitudes distintas). */
async function igualesSha256(a, b) {
  const codificador = new TextEncoder();
  const [hashA, hashB] = await Promise.all([
    crypto.subtle.digest("SHA-256", codificador.encode(a)),
    crypto.subtle.digest("SHA-256", codificador.encode(b)),
  ]);
  return crypto.subtle.timingSafeEqual(hashA, hashB);
}

/** Default-deny (RS06): devuelve el id de la clave o null. El secret API_KEYS
 * tiene el formato "id1:clave1,id2:clave2"; la clave viaja solo en header. */
async function autenticar(request, env) {
  const presentada = request.headers.get("x-api-key");
  if (!presentada || !env.API_KEYS) return null;
  for (const par of env.API_KEYS.split(",")) {
    const separador = par.indexOf(":");
    if (separador <= 0) continue;
    const id = par.slice(0, separador).trim();
    const clave = par.slice(separador + 1).trim();
    if (await igualesSha256(presentada, clave)) return id;
  }
  return null;
}

async function leerJson(env, claveObjeto) {
  const objeto = await env.BUCKET.get(claveObjeto);
  return objeto === null ? null : await objeto.json();
}

async function manejarApi(request, env, url) {
  const idClave = await autenticar(request, env);
  if (idClave === null) {
    console.log(JSON.stringify({ evento: "auth_rechazada", ruta: url.pathname })); // RS11: jamás la clave
    return respuestaApi({ error: "no autenticado" }, 401);
  }
  console.log(JSON.stringify({ evento: "acceso", clave_id: idClave, ruta: url.pathname })); // RS11

  const indice = await leerJson(env, "publicacion/indice.json");
  if (indice === null) {
    return respuestaApi({ error: "publicación no disponible" }, 404);
  }
  const publicacion = { sha256: indice.sha256, generado_en: indice.generado_en }; // RF17

  if (url.pathname === "/api/tasas") return manejarTasas(url, env, publicacion);
  if (url.pathname === "/api/jornadas/ultima") {
    const ultima = await leerJson(env, "publicacion/ultima.json");
    if (ultima === null) return respuestaApi({ error: "publicación no disponible" }, 404);
    return respuestaApi({ jornadas: [ultima], publicacion });
  }
  if (url.pathname === "/api/monedas") {
    const catalogo = await leerJson(env, "publicacion/monedas.json");
    if (catalogo === null) return respuestaApi({ error: "publicación no disponible" }, 404);
    return respuestaApi({ monedas: catalogo.monedas, publicacion });
  }
  return respuestaApi({ error: "ruta no encontrada" }, 404);
}

/** Validación estricta de parámetros (RS08): allowlist de nombres, formatos
 * cerrados y topes; el mapeo a claves de objeto R2 es cerrado (sin rutas
 * derivadas de entrada libre). */
function validarParametros(url) {
  const parametros = url.searchParams;
  for (const nombre of parametros.keys()) {
    if (!["fecha", "desde", "hasta", "moneda", "pagina", "limite", "descarga"].includes(nombre)) {
      return { error: "parámetro no reconocido" };
    }
  }
  const fecha = parametros.get("fecha");
  const desde = parametros.get("desde");
  const hasta = parametros.get("hasta");
  const moneda = parametros.get("moneda");
  const descarga = parametros.get("descarga");

  const fechaValida = (v) => RE_FECHA.test(v) && !Number.isNaN(Date.parse(v));
  for (const v of [fecha, desde, hasta]) {
    if (v !== null && !fechaValida(v)) return { error: "fecha inválida (se espera AAAA-MM-DD)" };
  }
  if (moneda !== null && !RE_MONEDA.test(moneda)) return { error: "moneda inválida" };
  if (descarga !== null && descarga !== "true" && descarga !== "false") {
    return { error: "descarga inválida" };
  }

  const esPuntual = fecha !== null;
  const esRango = desde !== null || hasta !== null;
  if (esPuntual === esRango) return { error: "se espera fecha o desde+hasta" };
  if (esRango && (desde === null || hasta === null)) return { error: "rango incompleto" };
  if (esRango && moneda === null) return { error: "el rango requiere moneda" };
  if (esRango && desde > hasta) return { error: "rango invertido" };

  const pagina = parametros.get("pagina") ?? "1";
  const limite = parametros.get("limite") ?? String(LIMITE_MAX);
  if (!RE_ENTERO.test(pagina) || Number(pagina) < 1) return { error: "página inválida" };
  if (!RE_ENTERO.test(limite) || Number(limite) < 1 || Number(limite) > LIMITE_MAX) {
    return { error: "límite inválido (1 a " + LIMITE_MAX + ")" };
  }

  return {
    fecha, desde, hasta, moneda,
    pagina: Number(pagina),
    limite: Number(limite),
    descarga: descarga === "true",
  };
}

async function manejarTasas(url, env, publicacion) {
  const parametros = validarParametros(url);
  if (parametros.error) return respuestaApi({ error: parametros.error }, 400);
  const { fecha, desde, hasta, moneda, pagina, limite, descarga } = parametros;

  if (fecha !== null) {
    const jornada = await leerJson(env, `publicacion/jornadas/${fecha}.json`);
    if (jornada === null) return respuestaApi({ error: "sin jornada para esa fecha" }, 404);
    let tasas = jornada.tasas;
    if (moneda !== null) {
      tasas = tasas.filter((t) => t.moneda === moneda);
      if (tasas.length === 0) return respuestaApi({ error: "moneda sin tasa en esa jornada" }, 404);
    }
    const cuerpo = { jornadas: [{ ...jornada, tasas }], publicacion };
    return respuestaApi(cuerpo, 200, descarga ? adjunto(`tasas_${fecha}.json`) : {});
  }

  const serie = await leerJson(env, `publicacion/series/${moneda}.json`);
  if (serie === null) return respuestaApi({ error: "moneda sin serie publicada" }, 404);
  const filas = serie.filas.filter(
    (f) => f.fecha_operacion >= desde && f.fecha_operacion <= hasta, // ISO: orden lexicográfico
  );
  const paginaFilas = filas.slice((pagina - 1) * limite, pagina * limite);
  const cuerpo = {
    jornadas: paginaFilas.map((f) => ({
      fecha_operacion: f.fecha_operacion,
      fecha_valor: f.fecha_valor,
      publicado_en: f.publicado_en,
      escala_monetaria: f.escala_monetaria,
      tasas: [{
        moneda: serie.moneda,
        usd_bid: f.usd_bid,
        usd_ask: f.usd_ask,
        bs_bid: f.bs_bid,
        bs_ask: f.bs_ask,
        cotizacion_invertida: f.cotizacion_invertida,
      }],
    })),
    paginacion: { pagina, limite, total_filas: filas.length },
    publicacion,
  };
  return respuestaApi(
    cuerpo, 200, descarga ? adjunto(`tasas_${moneda}_${desde}_${hasta}.json`) : {},
  );
}

function adjunto(nombre) {
  return { "content-disposition": `attachment; filename="${nombre}"` }; // RF13
}
