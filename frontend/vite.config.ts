import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  base: "/static/",
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    manifest: "manifest.json",
    outDir: resolve("./assets"),
    rollupOptions: {
      // overwrite default .html entry
      input: 'src/main.tsx',
    },
  },
  // optimizeDeps: {
  //   include: ['@emotion/styled'],
  // },
})
