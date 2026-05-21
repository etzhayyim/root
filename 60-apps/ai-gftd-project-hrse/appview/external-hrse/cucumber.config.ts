// @etzhayyim/cyber-freelance#CucumberConfig
// Cucumber設定ファイル

import { IConfiguration } from "@cucumber/cucumber";

export default {
	require: ["features/**/*.ts"],
	format: [
		"@cucumber/pretty-formatter",
		"json:reports/cucumber-report.json",
		"html:reports/cucumber-report.html",
	],
	formatOptions: {
		snippetInterface: "async-await",
	},
	worldParameters: {
		appUrl: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
	},
	publish: false,
} satisfies Partial<IConfiguration>;




