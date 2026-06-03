// vite.config.ts
import { sveltekit } from "file:///Users/junkawasaki/etzhayyim/etzhayyim-kyber/apps/etzhayyim-sheets/node_modules/.deno/@sveltejs+kit@2.49.4/node_modules/@sveltejs/kit/src/exports/vite/index.js";
import { paraglideVitePlugin } from "file:///Users/junkawasaki/etzhayyim/etzhayyim-kyber/apps/etzhayyim-sheets/node_modules/.deno/@inlang+paraglide-js@2.8.0/node_modules/@inlang/paraglide-js/dist/index.js";
import { defineConfig } from "file:///Users/junkawasaki/etzhayyim/etzhayyim-kyber/apps/etzhayyim-sheets/node_modules/.deno/vite@6.4.1/node_modules/vite/dist/node/index.js";
var vite_config_default = defineConfig({
  plugins: [
    sveltekit(),
    paraglideVitePlugin({
      project: "./project.inlang",
      outdir: "./src/lib/paraglide",
      strategy: ["url", "cookie", "baseLocale"]
    })
  ],
  server: {
    port: 3e3,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlUm9vdCI6ICIvVXNlcnMvanVua2F3YXNha2kvZ2Z0ZGNvanAvYWktZ2Z0ZC1reWJlci9hcHBzL2FpLWdmdGQtc2hlZXRzLyIsCiAgInNvdXJjZXNDb250ZW50IjogWyJjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZGlybmFtZSA9IFwiL1VzZXJzL2p1bmthd2FzYWtpL2dmdGRjb2pwL2FpLWdmdGQta3liZXIvYXBwcy9haS1nZnRkLXNoZWV0c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiL1VzZXJzL2p1bmthd2FzYWtpL2dmdGRjb2pwL2FpLWdmdGQta3liZXIvYXBwcy9haS1nZnRkLXNoZWV0cy92aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vVXNlcnMvanVua2F3YXNha2kvZ2Z0ZGNvanAvYWktZ2Z0ZC1reWJlci9hcHBzL2FpLWdmdGQtc2hlZXRzL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgc3ZlbHRla2l0IH0gZnJvbSAnQHN2ZWx0ZWpzL2tpdC92aXRlJztcbmltcG9ydCB7IHBhcmFnbGlkZVZpdGVQbHVnaW4gfSBmcm9tICdAaW5sYW5nL3BhcmFnbGlkZS1qcyc7XG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJztcblxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcblx0cGx1Z2luczogW1xuXHRcdHN2ZWx0ZWtpdCgpLFxuXHRcdHBhcmFnbGlkZVZpdGVQbHVnaW4oe1xuXHRcdFx0cHJvamVjdDogJy4vcHJvamVjdC5pbmxhbmcnLFxuXHRcdFx0b3V0ZGlyOiAnLi9zcmMvbGliL3BhcmFnbGlkZScsXG5cdFx0XHRzdHJhdGVneTogWyd1cmwnLCAnY29va2llJywgJ2Jhc2VMb2NhbGUnXSxcblx0XHR9KSxcblx0XSxcblx0c2VydmVyOiB7XG5cdFx0cG9ydDogMzAwMCxcblx0XHRob3N0OiAnMC4wLjAuMCcsXG5cdFx0cHJveHk6IHtcblx0XHRcdCcvYXBpJzoge1xuXHRcdFx0XHR0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjgwODAnLFxuXHRcdFx0XHRjaGFuZ2VPcmlnaW46IHRydWVcblx0XHRcdH1cblx0XHR9XG5cdH1cbn0pO1xuXG5cblxuXG5cblxuXG5cblxuXG5cblxuXG5cblxuXG5cbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBeVcsU0FBUyxpQkFBaUI7QUFDblksU0FBUywyQkFBMkI7QUFDcEMsU0FBUyxvQkFBb0I7QUFFN0IsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDM0IsU0FBUztBQUFBLElBQ1IsVUFBVTtBQUFBLElBQ1Ysb0JBQW9CO0FBQUEsTUFDbkIsU0FBUztBQUFBLE1BQ1QsUUFBUTtBQUFBLE1BQ1IsVUFBVSxDQUFDLE9BQU8sVUFBVSxZQUFZO0FBQUEsSUFDekMsQ0FBQztBQUFBLEVBQ0Y7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNQLE1BQU07QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNOLFFBQVE7QUFBQSxRQUNQLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNmO0FBQUEsSUFDRDtBQUFBLEVBQ0Q7QUFDRCxDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
