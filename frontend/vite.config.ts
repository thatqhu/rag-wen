import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",  // 监听 0.0.0.0，这对 Docker 至关重要
    port: 5173
  }
})
