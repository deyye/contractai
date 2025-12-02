import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // <--- 关键：允许外部 IP 访问
    port: 5173,      // 确保端口固定
    proxy: {
      '/api': {
        target: 'http://localhost:8001', // 后端地址
        changeOrigin: true,
      }
    }
  }
})