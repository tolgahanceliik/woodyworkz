import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // API isteklerini FastAPI'ye yönlendir (CORS bypass)
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/generated": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
