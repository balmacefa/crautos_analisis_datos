import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      lines: 85,
      functions: 85,
      branches: 85,
      statements: 85,
      include: ['src/components/**/*.{js,jsx}'],
      exclude: ['src/components/**/*.test.{js,jsx}']
    },
    include: ['src/components/**/*.test.{js,jsx}']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
