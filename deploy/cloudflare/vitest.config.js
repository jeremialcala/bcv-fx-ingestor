import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

// El binding BUCKET y la compatibility_date se heredan de wrangler.toml; el
// secret API_KEYS no vive en el toml (RS07), así que se inyecta aquí solo
// para las pruebas (formato "id:clave,id2:clave2", como el secret real).
export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.toml" },
      miniflare: {
        bindings: {
          API_KEYS: "analista-prueba:clave-secreta-de-prueba,segunda:otra-clave",
        },
      },
    }),
  ],
  test: {},
});
