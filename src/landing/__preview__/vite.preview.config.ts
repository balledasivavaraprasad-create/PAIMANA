import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

/**
 * Isolated dev config for previewing the public landing page on its own.
 *
 * Development scaffolding only — not part of the delivered page and not used by
 * the authenticated application's `vite.config.ts`. It exists so the landing
 * page can be opened in a browser without the app shell or auth redirect in
 * front of it.
 *
 * Run from this directory's parent (the `frontend` root):
 *   npx vite --config landing/__preview__/vite.preview.config.ts
 */
export default defineConfig({
  root: path.resolve(import.meta.dirname),
  publicDir: false,
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 4321,
    strictPort: false,
    open: false,
  },
  build: {
    outDir: path.resolve(import.meta.dirname, '../../.landing-preview-dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(import.meta.dirname, 'index.html'),
    },
  },
});