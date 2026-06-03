// @etzhayyim/cyber-freelance#CucumberHooks
// Cucumber hooks for timeout and setup

import { setDefaultTimeout } from "@cucumber/cucumber";

// Set default timeout to 60 seconds (60000 milliseconds) for integration tests
setDefaultTimeout(60 * 1000);

// 環境変数の設定（循環依存を避けるため、ここで直接設定）
if (!process.env.DATABASE_URL) {
	process.env.DATABASE_URL = "postgresql://placeholder:placeholder@localhost:5432/placeholder" /* placeholder */;
}

if (!process.env.CONNECT_API_URL) {
	process.env.CONNECT_API_URL = "http://localhost:8083";
}

if (!process.env.GRAPHQL_API_URL) {
	process.env.GRAPHQL_API_URL = "http://localhost:8082/graphql";
}

if (!process.env.OPENAI_API_KEY && !process.env.OPENROUTER_API_KEY_251025) {
	process.env.OPENAI_API_KEY = "test-api-key-for-coverage";
}

if (!process.env.NEXT_PUBLIC_APP_URL) {
	process.env.NEXT_PUBLIC_APP_URL = "http://localhost:3000";
}
