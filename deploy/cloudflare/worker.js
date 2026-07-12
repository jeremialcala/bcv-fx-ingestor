/**
 * Worker de distribución del artefacto bcv_fx.db desde R2 (edge-first).
 *
 * Solo distribución: NO expone API de consulta sobre los datos (no-scope del PRD,
 * ADR-0006). El CronJob de K8s publica el artefacto en el bucket R2 y este Worker
 * lo sirve globalmente con caché.
 *
 * Rutas:
 *   GET /bcv_fx.db  -> el archivo SQLite (attachment, con ETag y caché de 1 h)
 *   GET /estado     -> metadatos del artefacto publicado (JSON)
 */
const OBJETO = "bcv_fx.db";

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

    return new Response("rutas disponibles: /bcv_fx.db, /estado", { status: 404 });
  },
};
