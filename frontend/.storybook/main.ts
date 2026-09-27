import type { StorybookConfig } from '@storybook/react-vite'

// Reuses the app's vite.config.ts (React + Tailwind plugins), so stories are
// styled by exactly the same tokens and build pipeline as the app.
const config: StorybookConfig = {
  framework: '@storybook/react-vite',
  stories: ['../src/**/*.mdx', '../src/**/*.stories.tsx'],
  addons: ['@storybook/addon-docs', '@storybook/addon-a11y'],
  core: { disableTelemetry: true },
  // Storybook's own runtime, doc blocks and axe-core (a11y addon) are each
  // 0.5-1 MB. That's expected for a local dev tool no end user downloads, so
  // the warning is raised here only; the app build keeps Vite's default.
  viteFinal: (viteConfig) => ({
    ...viteConfig,
    build: { ...viteConfig.build, chunkSizeWarningLimit: 1200 },
  }),
}

export default config
