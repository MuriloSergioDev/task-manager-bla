import { defineConfig, mergeConfig } from 'vitest/config'

import viteConfig from './vite.config.ts'

// Date logic (e.g. "is this task overdue?") must use the viewer's local
// calendar day, not UTC. Pinning a zone that differs from UTC (UTC-3, no DST)
// makes that testable and identical on every machine, CI included. Set here,
// before any worker starts, so every test process inherits it.
process.env.TZ = 'America/Sao_Paulo'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['src/**/*.test.{ts,tsx}'],
      setupFiles: ['./src/test/setup.ts'],
      restoreMocks: true,
      coverage: {
        provider: 'v8',
        include: ['src/**/*.{ts,tsx}'],
        exclude: ['src/**/*.stories.tsx', 'src/**/*.test.{ts,tsx}', 'src/test/**', 'src/main.tsx', 'src/styles/foundations.tsx'],
        reporter: ['text-summary', 'text'],
      },
    },
  }),
)
