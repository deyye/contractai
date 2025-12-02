// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // 关键修复：排除 pdfjs-dist，防止 Vite 预构建破坏 Worker 文件
    exclude: ['pdfjs-dist'] 
  },
  server: {
    host: '0.0.0.0', 
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8001', 
        changeOrigin: true,
      }
    }
  }
})