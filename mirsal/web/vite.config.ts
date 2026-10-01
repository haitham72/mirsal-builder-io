import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

// Built into the folder the stdlib server serves at "/" (no Node at runtime). `npm run dev` proxies the API to the Python server.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(here, "src") } },
  build: { outDir: path.resolve(here, "../mirsal/console/dist"), emptyOutDir: true },
  server: {
    port: 5173,
    proxy: Object.fromEntries(["/api", "/out", "/src", "/lib", "/proj", "/ui"].map((p) => [p, "http://127.0.0.1:8770"])),
  },
});
