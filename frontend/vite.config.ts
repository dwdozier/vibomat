import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { TanStackRouterVite } from '@tanstack/router-vite-plugin'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    TanStackRouterVite(),
  ],
  server: {
    allowedHosts: ['app.vibomat.com'],
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: false,
      }
    }
  }
})
