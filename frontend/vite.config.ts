import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// This machine already runs other projects on 8000/8001/8002 and 5173/5174/5175 —
// InfraManager uses 8010 (backend) and 5180 (frontend dev).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5180,
    strictPort: true,
    proxy: {
      "/api": { target: "http://localhost:8010", changeOrigin: true },
      "/health": { target: "http://localhost:8010", changeOrigin: true },
    },
  },
});
