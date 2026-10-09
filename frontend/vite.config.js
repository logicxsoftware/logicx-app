import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

export default defineConfig({
  base: '/assets/logicx_app/frontend/',
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    outDir: '../logicx_app/public/frontend',
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@codexsun/ui/globals.css': path.resolve(__dirname, 'src/ui/src/styles/globals.css'),
      '@codexsun/ui': path.resolve(__dirname, 'src/ui/src'),
    },
  },
})
