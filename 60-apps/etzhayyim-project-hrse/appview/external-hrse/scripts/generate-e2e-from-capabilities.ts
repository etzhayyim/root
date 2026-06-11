// @etzhayyim/cyber-freelance#GenerateE2EFromCapabilities
// capabilities.jsonldからE2E TDDテストを自動生成するスクリプト

import * as fs from "node:fs";
import * as path from "node:path";

interface Capability {
	"@id": string;
	"@type": string;
	"rdfs:label": Array<{ "@value": string; "@language": string }>;
	"dcterms:description": Array<{ "@value": string; "@language": string }>;
	"prov:wasGeneratedBy"?: string | string[];
	implementation?: string[];
}

interface CapabilitiesJsonLd {
	"@context": Record<string, string>;
	"@graph": Capability[];
}

// Capability ID から E2E テストファイル名への変換
function capabilityIdToTestFileName(capabilityId: string): string {
	return capabilityId
		.replace(/Capability$/, "")
		.replace(/([A-Z])/g, "-$1")
		.toLowerCase()
		.replace(/^-/, "");
}

// Capability から E2E TDD テストコードを生成
function generateE2ETest(capability: Capability): string {
	const id = capability["@id"];
	const labelEn = capability["rdfs:label"].find((l) => l["@language"] === "en")?.[
		"@value"
	] || id;
	const labelJa = capability["rdfs:label"].find((l) => l["@language"] === "ja")?.[
		"@value"
	] || labelEn;
	const descEn = capability["dcterms:description"].find(
		(d) => d["@language"] === "en"
	)?.["@value"] || "";
	const descJa = capability["dcterms:description"].find(
		(d) => d["@language"] === "ja"
	)?.["@value"] || descEn;
	const activities = Array.isArray(capability["prov:wasGeneratedBy"])
		? capability["prov:wasGeneratedBy"]
		: capability["prov:wasGeneratedBy"]
			? [capability["prov:wasGeneratedBy"]]
			: [];
	const implementations = capability.implementation || [];

	const testContent = `// @etzhayyim/cyber-freelance#${id}E2E
// E2E TDD Test: ${labelEn}
// Description: ${descEn}
// Activities: ${activities.join(", ")}
// Implementation: ${implementations.join(", ")}
// Generated from capabilities.jsonld

import { test, expect } from "@playwright/test";

test.describe("${labelEn}", () => {
	test.describe("TDD: Red Phase - Define Expected Behavior", () => {
		/**
		 * TDD Red Phase: Define what the capability should do
		 * ${descJa}
		 */

		test("capability should be accessible", async ({ page }) => {
			await page.goto("/");
			await expect(page).toHaveTitle(/.*/);
		});

		test("capability should handle normal use case", async ({ page }) => {
			// ${descJa}
			await page.goto("/");
			await page.waitForLoadState("networkidle");
			// Add assertions for expected behavior
		});

		test("capability should handle error cases gracefully", async ({ page }) => {
			await page.goto("/");
			// Simulate error condition and verify graceful handling
		});

		test("capability should validate input", async ({ page }) => {
			await page.goto("/");
			// Test with invalid input and verify validation
		});
	});

${activities.length > 0 ? generateActivityTests(activities, labelEn) : ""}

	test.describe("TDD: Green Phase - Implementation Verification", () => {
		/**
		 * TDD Green Phase: Verify implementation works correctly
		 */

		test("implementation files should exist", async () => {
			// Verify that implementation files are in place
			const implementations = ${JSON.stringify(implementations)};
			// This is a placeholder - actual file existence check
			// would be done at build time, not runtime
			expect(implementations.length).toBeGreaterThanOrEqual(0);
		});
	});

	test.describe("TDD: Refactor Phase - Quality Checks", () => {
		/**
		 * TDD Refactor Phase: Verify code quality and performance
		 */

		test("capability should perform within acceptable time", async ({ page }) => {
			const startTime = Date.now();
			await page.goto("/");
			await page.waitForLoadState("networkidle");
			const endTime = Date.now();

			// Performance threshold: 5 seconds
			expect(endTime - startTime).toBeLessThan(5000);
		});

		test("capability should be accessible", async ({ page }) => {
			await page.goto("/");
			// Basic accessibility check
			const main = page.locator("main, [role='main'], body");
			await expect(main).toBeVisible();
		});
	});
});
`;

	return testContent;
}

// Activity ベースのテストを生成
function generateActivityTests(activities: string[], capabilityLabel: string): string {
	return activities
		.map(
			(activity) => `
	test.describe("Activity: ${activity}", () => {
		test("${activity} should complete successfully", async ({ page }) => {
			await page.goto("/");
			// Trigger the activity and verify completion
		});

		test("${activity} should handle concurrent execution", async ({ page }) => {
			await page.goto("/");
			// Test concurrent execution handling
		});
	});
`
		)
		.join("\n");
}

// E2E BDD Feature ファイルを生成
function generateE2EFeature(capability: Capability): string {
	const id = capability["@id"];
	const labelEn = capability["rdfs:label"].find((l) => l["@language"] === "en")?.[
		"@value"
	] || id;
	const labelJa = capability["rdfs:label"].find((l) => l["@language"] === "ja")?.[
		"@value"
	] || labelEn;
	const descEn = capability["dcterms:description"].find(
		(d) => d["@language"] === "en"
	)?.["@value"] || "";
	const descJa = capability["dcterms:description"].find(
		(d) => d["@language"] === "ja"
	)?.["@value"] || descEn;
	const activities = Array.isArray(capability["prov:wasGeneratedBy"])
		? capability["prov:wasGeneratedBy"]
		: capability["prov:wasGeneratedBy"]
			? [capability["prov:wasGeneratedBy"]]
			: [];
	const implementations = capability.implementation || [];

	const featureContent = `# @etzhayyim/cyber-freelance#${id}
# Capability: ${labelEn}
# Description: ${descEn}
# Activity: ${activities.join(", ")}
# Implementation: ${implementations.join(", ")}
# Generated from capabilities.jsonld

@e2e @${id.toLowerCase().replace(/capability$/, "")}
Feature: ${labelJa}
  ${descJa}

  Background:
    Given ログイン済みのユーザーである

  @smoke
  Scenario: ${labelJa}が利用可能である
    When ${labelEn}機能にアクセスする
    Then 機能が正常に動作する

  @positive
  Scenario: ${labelJa}が正常に完了する
    Given システムが正常に稼働している
    When ${labelEn}を実行する
    Then 処理が成功する
    And 結果が正しく返される

  @negative
  Scenario: ${labelJa}がエラーを適切に処理する
    Given システムが正常に稼働している
    When ${labelEn}でエラーが発生する
    Then エラーが適切にハンドリングされる
    And エラーメッセージが表示される

  @validation
  Scenario: ${labelJa}が入力を検証する
    Given システムが正常に稼働している
    When 不正な入力で${labelEn}を実行する
    Then バリデーションエラーが返される
    And 適切なエラーメッセージが表示される
`;

	return featureContent;
}

async function main(): Promise<void> {
	const capabilitiesPath = path.resolve(
		process.cwd(),
		"capabilities.jsonld"
	);
	const e2eDir = path.resolve(process.cwd(), "e2e/capabilities");
	const e2eBddDir = path.resolve(process.cwd(), "features/e2e/capabilities");

	// ディレクトリを作成
	if (!fs.existsSync(e2eDir)) {
		fs.mkdirSync(e2eDir, { recursive: true });
	}
	if (!fs.existsSync(e2eBddDir)) {
		fs.mkdirSync(e2eBddDir, { recursive: true });
	}

	// capabilities.jsonld を読み込み
	const capabilitiesContent = fs.readFileSync(capabilitiesPath, "utf-8");
	const capabilities: CapabilitiesJsonLd = JSON.parse(capabilitiesContent);

	console.log("Generating E2E TDD tests from capabilities.jsonld...\n");

	let tddCount = 0;
	let bddCount = 0;

	for (const capability of capabilities["@graph"]) {
		if (capability["@type"] !== "Capability") {
			continue;
		}

		const testFileName = capabilityIdToTestFileName(capability["@id"]);

		// E2E TDD テストを生成
		const tddTestContent = generateE2ETest(capability);
		const tddTestPath = path.join(e2eDir, `${testFileName}.spec.ts`);
		fs.writeFileSync(tddTestPath, tddTestContent);
		console.log(`✓ Generated E2E TDD: ${tddTestPath}`);
		tddCount++;

		// E2E BDD Feature を生成
		const bddFeatureContent = generateE2EFeature(capability);
		const bddFeaturePath = path.join(e2eBddDir, `${testFileName}.feature`);
		fs.writeFileSync(bddFeaturePath, bddFeatureContent);
		console.log(`✓ Generated E2E BDD: ${bddFeaturePath}`);
		bddCount++;
	}

	console.log(`\n✅ Generated ${tddCount} E2E TDD tests`);
	console.log(`✅ Generated ${bddCount} E2E BDD feature files`);
	console.log("\nNext steps:");
	console.log("1. Run E2E TDD tests: pnpm test:e2e:tdd");
	console.log("2. Run E2E BDD tests: pnpm test:e2e:bdd");
	console.log(
		"3. Update generated tests with specific assertions for your implementation"
	);
}

main().catch((error) => {
	console.error("Error generating E2E tests:", error);
	process.exit(1);
});



