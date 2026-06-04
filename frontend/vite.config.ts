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
    outDir: resolve("./dist"),
    rollupOptions: {
      input: {
        // Main React application entry.
        main: 'src/main.tsx',
        // Separate CSS-only entry for PDF file-type icons.
        // Tailwind V4 scans models.py + the PDF template (via @source in pdf-icons.css)
        // and generates CSS only for the icon classes actually referenced there.
        // Adding a new file type: update _EXTENSION_TO_ICON_CLASS in models.py and rebuild.
        'pdf-icons': resolve('./src/pdf-icons.css'),
      },
      output: {
        // Give the PDF icon CSS a stable, hash-free name so Django's staticfiles
        // finder can always locate it as 'pdf-icons.css'.
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'pdf-icons.css') return 'pdf-icons.css';
          return 'assets/[name]-[hash][extname]';
        },
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
      },
    },
  },
  // optimizeDeps: {
  //   include: ['@emotion/styled'],
  // },
})
