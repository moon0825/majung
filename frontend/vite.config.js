import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  // 기본 "/"(단일 오리진 컨테이너 배포·개발). GitHub Pages 프로젝트 배포 시
  // VITE_BASE=/majung/ 로 빌드한다(자산 경로를 서브패스에 맞춤).
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 백엔드 오케스트레이터(MCP 호스트)로 프록시
      "/api": { target: "http://localhost:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
    },
  },
});
