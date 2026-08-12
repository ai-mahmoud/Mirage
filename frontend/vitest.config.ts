import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

// Separate from vite.config.ts (not merged in) because `vite`'s own
// defineConfig doesn't know about the `test` key — keeping them apart
// avoids fighting the production build's type-checking for a dev-only
// concern. Aliases/plugins are duplicated rather than shared since
// there are only two lines of overlap.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
})
