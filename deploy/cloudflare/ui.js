/**
 * Web UI mínima de consulta y descarga (RF14, FX-ING-002).
 *
 * Self-contained: CSS y JS inline (la CSP del Worker prohíbe todo origen
 * externo; el 'unsafe-inline' es el costo de servirla como un solo string).
 * La clave API vive SOLO en memoria (nunca sessionStorage/localStorage/URL,
 * RS07/RF15) y viaja siempre en el header X-Api-Key; la descarga usa
 * fetch + blob para no ponerla jamás en una URL. La tabla se construye con
 * createElement/textContent — nunca innerHTML con datos (XSS).
 */
export const PAGINA_HTML = `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BCV FX — consulta de tasas</title>
<style>
  :root { color-scheme: light dark; font-family: system-ui, sans-serif; }
  body { margin: 2rem auto; max-width: 60rem; padding: 0 1rem; line-height: 1.4; }
  h1 { font-size: 1.3rem; }
  fieldset { border: 1px solid #8884; border-radius: .5rem; margin-bottom: 1rem; }
  label { display: inline-block; margin-right: 1rem; }
  input, select, button { font: inherit; padding: .25rem .5rem; }
  button { cursor: pointer; }
  table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
  th, td { border: 1px solid #8884; padding: .3rem .5rem; text-align: right; }
  th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) { text-align: left; }
  #estado { margin: .5rem 0; }
  #estado.error { color: #b30000; }
  footer { margin-top: 1.5rem; font-size: .8rem; opacity: .7; }
  .oculto { display: none; }
</style>
</head>
<body>
<h1>BCV FX — consulta de tasas de referencia</h1>
<p>Consulta de solo lectura sobre la publicación oficial derivada del artefacto
<code>bcv_fx.db</code>. Requiere una clave API (header <code>X-Api-Key</code>).</p>

<fieldset>
  <legend>Acceso</legend>
  <label>Clave API <input type="password" id="clave" autocomplete="off"></label>
  <button id="conectar">Conectar</button>
</fieldset>

<fieldset id="consulta" class="oculto">
  <legend>Consulta</legend>
  <label>Modo
    <select id="modo">
      <option value="ultima">Última jornada</option>
      <option value="fecha">Fecha puntual</option>
      <option value="rango">Rango (serie)</option>
    </select>
  </label>
  <label>Moneda <select id="moneda"><option value="">todas</option></select></label>
  <label id="campo-fecha" class="oculto">Fecha <input type="date" id="fecha"></label>
  <label id="campo-desde" class="oculto">Desde <input type="date" id="desde"></label>
  <label id="campo-hasta" class="oculto">Hasta <input type="date" id="hasta"></label>
  <button id="consultar">Consultar</button>
  <button id="descargar" disabled>Descargar JSON</button>
</fieldset>

<div id="estado"></div>
<div id="resultado"></div>
<footer id="pie"></footer>

<script>
(() => {
  "use strict";
  let clave = null;        // solo en memoria: nunca se persiste (RS07)
  let ultimaUrl = null;    // última consulta exitosa, para descargar

  const $ = (id) => document.getElementById(id);
  const estado = (mensaje, esError) => {
    $("estado").textContent = mensaje || "";
    $("estado").className = esError ? "error" : "";
  };

  async function api(ruta) {
    const respuesta = await fetch(ruta, { headers: { "X-Api-Key": clave } });
    const cuerpo = await respuesta.json();
    if (!respuesta.ok) throw new Error(cuerpo.error || ("HTTP " + respuesta.status));
    return cuerpo;
  }

  $("modo").addEventListener("change", () => {
    const modo = $("modo").value;
    $("campo-fecha").classList.toggle("oculto", modo !== "fecha");
    $("campo-desde").classList.toggle("oculto", modo !== "rango");
    $("campo-hasta").classList.toggle("oculto", modo !== "rango");
  });

  $("conectar").addEventListener("click", async () => {
    clave = $("clave").value.trim();
    if (!clave) { estado("ingresa la clave API", true); return; }
    estado("conectando…");
    try {
      const cuerpo = await api("/api/monedas");
      const selector = $("moneda");
      selector.replaceChildren(new Option("todas", ""));
      for (const m of cuerpo.monedas) {
        selector.append(new Option(m.codigo + " — " + m.pais, m.codigo));
      }
      $("consulta").classList.remove("oculto");
      pie(cuerpo.publicacion);
      estado("conectado: " + cuerpo.monedas.length + " monedas disponibles");
    } catch (error) {
      clave = null;
      estado("no se pudo conectar: " + error.message, true);
    }
  });

  $("consultar").addEventListener("click", async () => {
    const modo = $("modo").value;
    const moneda = $("moneda").value;
    let url;
    if (modo === "ultima") {
      url = "/api/jornadas/ultima";
    } else if (modo === "fecha") {
      if (!$("fecha").value) { estado("elige una fecha", true); return; }
      url = "/api/tasas?fecha=" + $("fecha").value + (moneda ? "&moneda=" + moneda : "");
    } else {
      if (!$("desde").value || !$("hasta").value) { estado("elige el rango", true); return; }
      if (!moneda) { estado("el rango requiere una moneda", true); return; }
      url = "/api/tasas?desde=" + $("desde").value + "&hasta=" + $("hasta").value + "&moneda=" + moneda;
    }
    estado("consultando…");
    try {
      const cuerpo = await api(url);
      pintar(cuerpo.jornadas);
      pie(cuerpo.publicacion, cuerpo.paginacion);
      ultimaUrl = url;
      $("descargar").disabled = modo === "ultima"; // /jornadas/ultima no pagina descarga
      estado("");
    } catch (error) {
      estado(error.message, true);
      $("resultado").replaceChildren();
    }
  });

  $("descargar").addEventListener("click", async () => {
    if (!ultimaUrl) return;
    // fetch + blob: la clave va en el header, jamás en la URL del navegador (RS07)
    const separador = ultimaUrl.includes("?") ? "&" : "?";
    const respuesta = await fetch(ultimaUrl + separador + "descarga=true", {
      headers: { "X-Api-Key": clave },
    });
    if (!respuesta.ok) { estado("descarga fallida", true); return; }
    const nombre = (respuesta.headers.get("content-disposition") || "")
      .split('filename="')[1]?.replace('"', "") || "tasas.json";
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(await respuesta.blob());
    enlace.download = nombre;
    enlace.click();
    URL.revokeObjectURL(enlace.href);
  });

  function pintar(jornadas) {
    const tabla = document.createElement("table");
    const encabezado = tabla.createTHead().insertRow();
    for (const titulo of ["Fecha operación", "Moneda", "BID (M.E./US$)", "ASK (M.E./US$)", "BID (Bs./M.E.)", "ASK (Bs./M.E.)", "Invertida"]) {
      const th = document.createElement("th");
      th.textContent = titulo;
      encabezado.append(th);
    }
    const cuerpo = tabla.createTBody();
    for (const jornada of jornadas) {
      for (const tasa of jornada.tasas) {
        const fila = cuerpo.insertRow();
        for (const valor of [jornada.fecha_operacion, tasa.moneda, tasa.usd_bid, tasa.usd_ask, tasa.bs_bid, tasa.bs_ask, tasa.cotizacion_invertida ? "sí" : ""]) {
          fila.insertCell().textContent = String(valor);
        }
      }
    }
    $("resultado").replaceChildren(tabla);
  }

  function pie(publicacion, paginacion) {
    const partes = [];
    if (publicacion) {
      partes.push("publicación " + publicacion.generado_en + " · sha256 " + publicacion.sha256.slice(0, 12) + "…");
    }
    if (paginacion) {
      partes.push("página " + paginacion.pagina + " (" + paginacion.total_filas + " filas en total)");
    }
    $("pie").textContent = partes.join(" · ");
  }
})();
</script>
</body>
</html>`;
