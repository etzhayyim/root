import { defineConfig } from "vitest/config";
import path from "node:path";
const root = __dirname;
export default defineConfig({
  resolve: {
    alias: [
      { find: /^@gftd\/magatama-host-sdk$/, replacement: path.resolve(root, "../../../../20-actors/magatama/sdk/magatama-host-sdk/src/index.ts") },
      { find: /^@gftd\/magatama-host-sdk\/(.*)$/, replacement: path.resolve(root, "../../../../20-actors/magatama/sdk/magatama-host-sdk/src/$1") },
      { find: /^@gftd\/xrpc$/, replacement: path.resolve(root, "../../../../10-protocol/xrpc/src/index.ts") },
    ],
  },
  test: { globals: true, testTimeout: 15000 },
});
