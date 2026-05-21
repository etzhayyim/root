import { defineConfig } from "vite";
import { sveltekit } from "@sveltejs/kit/vite";

export default defineConfig({
  plugins: [sveltekit()],
  build: { outDir: "build" },
  server: {
    proxy: {
      "/xrpc": "https://mamoru.gftd.ai",
      "/health": "https://mamoru.gftd.ai",
    },
  },
});
