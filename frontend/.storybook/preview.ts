import type { Preview } from '@storybook/react-vite'

import '../src/index.css'

const preview: Preview = {
  parameters: {
    layout: 'centered',
    backgrounds: {
      options: {
        paper: { name: 'Paper (page)', value: '#e9ece6' },
        sheet: { name: 'Sheet (surface)', value: '#fafbf8' },
      },
    },
    // Fail the a11y panel loudly rather than just listing findings.
    a11y: { test: 'error' },
    controls: { expanded: true },
  },
  initialGlobals: {
    backgrounds: { value: 'paper' },
  },
  tags: ['autodocs'],
}

export default preview
