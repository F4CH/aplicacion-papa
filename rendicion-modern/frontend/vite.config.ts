import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.VITE_BACKEND_TARGET ?? "http://127.0.0.1:8010";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true
      },
      "/exportar": {
        target: backendTarget,
        changeOrigin: true
      },
      "/reportes": {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
});
