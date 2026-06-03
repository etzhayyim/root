// @etzhayyim/cyber-freelance#IntegrationSetup
// BDD統合テスト用のセットアップ

import { BeforeAll, AfterAll } from "@cucumber/cucumber";
import { execSync } from "child_process";

let servicesStarted = false;

async function unsupportedFetch(endpoint: string): Promise<never> {
	throw new Error(`Unsupported: fetch is disabled in hrse (${endpoint})`);
}

/**
 * HTTPサービスが起動しているか確認
 */
async function checkHttpServiceHealth(url: string, timeout = 30000): Promise<boolean> {
	const startTime = Date.now();
	while (Date.now() - startTime < timeout) {
		try {
			const response = await unsupportedFetch(url);
			if (response.ok || response.status === 404 || response.status === 405) {
				// 404や405でもサービスは起動している
				return true;
			}
		} catch (error) {
			// エラーが発生した場合は再試行
		}
		await new Promise((resolve) => setTimeout(resolve, 1000));
	}
	return false;
}

/**
 * PostgreSQLが起動しているか確認
 */
function checkPostgresHealth(timeout = 30000): boolean {
	const startTime = Date.now();
	while (Date.now() - startTime < timeout) {
		try {
			execSync("docker-compose exec -T postgres pgIsready -U postgres", {
				stdio: "ignore",
				cwd: process.cwd(),
			});
			return true;
		} catch (error) {
			// エラーが発生した場合は再試行
		}
		// 1秒待機（同期版）
		const start = Date.now();
		while (Date.now() - start < 1000) {
			// ビジーウェイト
		}
	}
	return false;
}

/**
 * Docker Composeサービスが起動しているか確認
 */
function checkDockerServices(): boolean {
	try {
		const output = execSync("docker-compose ps --services --filter 'status=running'", {
			encoding: "utf-8",
		});
		const runningServices = output.trim().split("\n").filter((s) => s.length > 0);
		return runningServices.length > 0;
	} catch (error) {
		return false;
	}
}

/**
 * バックエンドサービスを起動
 */
async function startBackendServices(): Promise<void> {
	if (checkDockerServices()) {
		console.log("✅ Docker Compose services are already running");
		return;
	}

	console.log("🚀 Starting backend services with docker-compose...");
	try {
		execSync("docker-compose up -d postgres connect-go", {
			stdio: "inherit",
			cwd: process.cwd(),
		});

		// サービスが起動するまで待機
		console.log("⏳ Waiting for services to be ready...");
		const postgresReady = checkPostgresHealth(60000);
		const connectReady = await checkHttpServiceHealth("http://localhost:8083", 60000);

		if (postgresReady && connectReady) {
			console.log("✅ Backend services are ready");
			servicesStarted = true;
		} else {
			throw new Error("Services failed to start within timeout");
		}
	} catch (error) {
		console.error("❌ Failed to start backend services:", error);
		throw error;
	}
}

/**
 * バックエンドサービスを停止
 */
function stopBackendServices(): void {
	if (!servicesStarted) {
		return;
	}

	console.log("🛑 Stopping backend services...");
	try {
		execSync("docker-compose stop postgres connect-go", {
			stdio: "inherit",
			cwd: process.cwd(),
		});
		console.log("✅ Backend services stopped");
	} catch (error) {
		console.error("⚠️  Failed to stop backend services:", error);
	}
}

// BeforeAll: すべてのテストの前にバックエンドサービスを起動
// 注意: 環境変数はhooks.tsで設定されるため、ここでは設定しない
BeforeAll(async function () {
	// バックエンドサービスを起動（オプション: 環境変数で制御可能）
	if (process.env.SKIP_SERVICE_START !== "true") {
		await startBackendServices();
	}
});

// AfterAll: すべてのテストの後にバックエンドサービスを停止（オプション）
// 注意: 他のテストが実行中の場合は停止しない
AfterAll(function () {
	// 環境変数で制御可能にする
	if (process.env.STOP_SERVICES_AFTER_TEST === "true") {
		stopBackendServices();
	}
});
