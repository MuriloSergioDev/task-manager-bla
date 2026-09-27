import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    watch: {
      // Bind-mounting the Windows host filesystem into the Linux container
      // (docker-compose.yml's `./frontend:/app`) doesn't reliably deliver
      // inotify events, so the dev server can silently keep serving a stale
      // bundle after a host-side edit. Polling trades a little CPU for
      // hot-reload actually firing.
      usePolling: true,
    },
  },
})
