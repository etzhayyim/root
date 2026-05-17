/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'node:url';

const rootDir = dirname(fileURLToPath(import.meta.url));
const r = (p: string) => resolve(rootDir, p);

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [r('./vitest.setup.ts')],
    include: ['packages/**/src/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['packages/**/src/**/*.{ts,tsx}'],
      exclude: ['**/node_modules/**', 'examples/**'],
      all: true,
      thresholds: {
        global: {
          branches: 100,
          functions: 100,
          lines: 100,
          statements: 100,
        },
      },
    },
  },
  resolve: {
    alias: {
      '@gftd/bpmn-sdk/core': resolve('./packages/core/src'),
      '@gftd/bpmn-sdk/dsl': resolve('./packages/dsl/src'),
      '@gftd/bpmn-sdk/compiler': resolve('./packages/compiler/src'),
      '@gftd/bpmn-sdk/runtime': resolve('./packages/runtime/src'),
      '@gftd/bpmn-sdk/importer': resolve('./packages/importer/src'),
      '@gftd/bpmn-sdk/human': resolve('./packages/human/src'),
      '@gftd/bpmn-sdk/validation': resolve('./packages/validation/src'),
      '@gftd/bpmn-sdk/testing': resolve('./packages/testing/src'),
      '@gftd/bpmn-sdk/ops': resolve('./packages/ops/src'),
      '@gftd/bpmn-sdk/form': resolve('./packages/form/src'),
      '@gftd/bpmn-sdk/dmn': resolve('./packages/dmn/src'),
      '@gftd/bpmn-sdk/testkit': resolve('./packages/internal/testkit/src'),
    },
  },
});

