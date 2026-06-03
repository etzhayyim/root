// @etzhayyim/cyber-freelance#ATDDGenerator
// capabilities.jsonldからATDDテストを生成

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

interface Capability {
	"@id": string;
	"@type": string;
	"rdfs:label": Array<{ "@value": string; "@language": string }>;
	"dcterms:description": Array<{ "@value": string; "@language": string }>;
	"prov:wasGeneratedBy"?: string;
	implementation?: string[];
}

interface CapabilitiesJSONLD {
	"@context": Record<string, string>;
	"@graph": Capability[];
}

/**
 * capabilities.jsonldを読み込む
 */
function loadCapabilities(filePath: string): CapabilitiesJSONLD {
	const content = readFileSync(filePath, "utf-8");
	return JSON.parse(content) as CapabilitiesJSONLD;
}

/**
 * CapabilityからATDDテストを生成
 */
function generateATDDTest(capability: Capability): string {
	const id = capability["@id"];
	const label = capability["rdfs:label"]?.find((l) => l["@language"] === "en")?.["@value"] || id;
	const description =
		capability["dcterms:description"]?.find((d) => d["@language"] === "en")?.["@value"] || "";
	const activity = capability["prov:wasGeneratedBy"] || "";

	// Capability IDからテストファイル名を生成
	const testFileName = id.replace(/Capability$/, "").replace(/([A-Z])/g, "-$1").toLowerCase().slice(1);

	return `// @etzhayyim/cyber-freelance#${id}
// ATDD Test: ${label}
// Generated from capabilities.jsonld

import { test, expect } from "@playwright/test";

/**
 * Capability: ${label}
 * Description: ${description}
 * Activity: ${activity}
 * Implementation: ${capability.implementation?.join(", ") || "N/A"}
 */
test.describe("${label}", () => {
	test("should implement ${label} capability", async ({ page }) => {
		// Given: ${label} capability is available
		// When: The capability is invoked
		// Then: It should perform the expected behavior

		// Example test structure:
		// await page.goto("/path/to/capability");
		// await expect(page.getByText("${label}")).toBeVisible();
	});

	test("should handle errors gracefully", async ({ page }) => {
		// Given: An error condition occurs
		// When: The capability is invoked
		// Then: It should handle the error appropriately

	});
});
`;
}

/**
 * ATDDテストファイルを生成
 */
function generateATDDTests(capabilities: CapabilitiesJSONLD, outputDir: string) {
	// 出力ディレクトリを作成
	mkdirSync(outputDir, { recursive: true });

	// 各Capabilityからテストを生成
	for (const capability of capabilities["@graph"]) {
		if (capability["@type"] === "Capability") {
			const testContent = generateATDDTest(capability);
			const testFileName = capability["@id"]
				.replace(/Capability$/, "")
				.replace(/([A-Z])/g, "-$1")
				.toLowerCase()
				.slice(1) + ".spec.ts";

			const outputPath = join(outputDir, testFileName);
			writeFileSync(outputPath, testContent, "utf-8");
			console.log(`✅ Generated: ${outputPath}`);
		}
	}
}

/**
 * メイン処理
 */
function main() {
	const capabilitiesPath = join(process.cwd(), "capabilities.jsonld");
	const outputDir = join(process.cwd(), "e2e", "atdd");

	console.log("📖 Loading capabilities.jsonld...");
	const capabilities = loadCapabilities(capabilitiesPath);

	console.log(`📦 Found ${capabilities["@graph"].length} capabilities`);
	console.log("🚀 Generating ATDD tests...");

	generateATDDTests(capabilities, outputDir);

	console.log(`✅ ATDD tests generated in ${outputDir}`);
}

main();





