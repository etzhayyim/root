// @etzhayyim/cyber-freelance#CucumberE2EConfig
// E2E BDD用のCucumber設定ファイル

import type { IConfiguration } from "@cucumber/cucumber";

export default {
	require: [
		"features/support/e2e-world.ts",
		"features/support/e2e-hooks.ts",
		"features/stepDefinitions/e2e-common.steps.ts",
	],
	paths: ["features/e2e/**/*.feature"],
	format: [
		"@cucumber/pretty-formatter",
		"json:reports/cucumber-e2e-report.json",
		"html:reports/cucumber-e2e-report.html",
	],
	formatOptions: {
		snippetInterface: "async-await",
	},
	worldParameters: {
		appUrl: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
		graphqlUrl: process.env.GRAPHQL_API_URL || "http://localhost:8082/graphql",
	},
	publish: false,
	// E2Eテストはタグで制御
	tags: "@e2e",
} satisfies Partial<IConfiguration>;



