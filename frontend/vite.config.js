import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts: ['victory'],
          markdown: ['react-markdown', 'remark-gfm'],
          codemirror: ['codemirror', '@codemirror/lang-javascript', '@codemirror/lang-python', '@codemirror/lang-java', '@codemirror/lang-cpp', '@codemirror/theme-one-dark'],
        }
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'json-summary'],
      reportOnFailure: true,
      thresholds: {
        statements: 20,
        branches: 13,
        functions: 14,
        lines: 22
      }
    }
  }
})
