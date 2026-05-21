import path from "node:path";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { TransformStream } from "stream/web";

// TransformStream polyfill for Node.js environments
if (typeof globalThis.TransformStream === "undefined") {
	globalThis.TransformStream = TransformStream as typeof globalThis.TransformStream;
}

export default defineConfig({
	plugins: [react()],
	define: {
		global: "globalThis",
	},
	test: {
		environment: "jsdom",
		setupFiles: ["./vitest.setup.ts"],
		globals: true,
		// メモリリーク対策: VMベースのプールを使用してメモリ制限を設定
		pool: "vmThreads",
		// メモリリーク対策: ワーカーのメモリ制限（300MBに削減）
		vmMemoryLimit: "300MB",
		// メモリリーク対策: テストの分離を有効化
		isolate: true,
		// メモリリーク対策: 並列実行数の制限（3に削減）
		maxConcurrency: 3,
		// メモリリーク対策: ワーカープロセスの最大数（2に削減）
		maxWorkers: 2,
		// メモリリーク対策: クリーンアップのタイムアウト
		teardownTimeout: 10000,
		// メモリリーク対策: 各テスト後のガベージコレクション
		forceRerunTriggers: [],
		// メモリリーク対策: テストファイルごとにワーカーを再利用しない
		poolOptions: {
			vmThreads: {
				singleThread: false,
			},
		},
		coverage: {
			provider: "v8",
			reporter: ["text", "json", "html", "lcov"],
			exclude: [
				"nodeModules/",
				"**/*.config.*",
				"**/vitest.setup.ts",
				"**/*.test.{ts,tsx}",
				"**/*.spec.{ts,tsx}",
				"**/generated/**",
				"**/e2e/**",
			],
			include: ["src/**/*.{ts,tsx}"],
			thresholds: {
				lines: process.env.VITEST_COVERAGE_THRESHOLD ? Number(process.env.VITEST_COVERAGE_THRESHOLD) : 100,
				functions: process.env.VITEST_COVERAGE_THRESHOLD ? Number(process.env.VITEST_COVERAGE_THRESHOLD) : 100,
				branches: process.env.VITEST_COVERAGE_THRESHOLD ? Number(process.env.VITEST_COVERAGE_THRESHOLD) : 100,
				statements: process.env.VITEST_COVERAGE_THRESHOLD ? Number(process.env.VITEST_COVERAGE_THRESHOLD) : 100,
			},
		},
		// CI環境ではwatchを無効化
		watch: process.env.CI !== "1",
		ui: process.env.CI !== "1",
		reporters: process.env.CI === "1" ? ["dot"] : ["default"],
		testTimeout: 10000,
		hookTimeout: 10000,
	},
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
});
