// @etzhayyim/cyber-freelance#BDDGenerator
// capabilities.jsonldからCucumber BDD featureファイルを生成

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

interface Capability {
	"@id": string;
	"@type": string;
	"rdfs:label": Array<{ "@value": string; "@language": string }>;
	"dcterms:description": Array<{ "@value": string; "@language": string }>;
	"prov:wasGeneratedBy"?: string | string[];
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
 * CapabilityからCucumber featureファイルを生成
 */
function generateFeatureFile(capability: Capability): string {
	const id = capability["@id"];
	const label = capability["rdfs:label"]?.find((l) => l["@language"] === "en")?.["@value"] || id;
	const description =
		capability["dcterms:description"]?.find((d) => d["@language"] === "en")?.["@value"] || "";
	const activity = capability["prov:wasGeneratedBy"] || "";
	const implementation = capability.implementation || [];

	// Capability IDからfeatureファイル名を生成
	const featureName = id.replace(/Capability$/, "").replace(/([A-Z])/g, "-$1").toLowerCase().slice(1);

	// Given-When-Thenシナリオを生成
	const scenarios = generateScenarios(capability, label, description);

	return `# @etzhayyim/cyber-freelance#${id}
# Capability: ${label}
# Description: ${description}
# Activity: ${Array.isArray(activity) ? activity.join(", ") : activity}
# Implementation: ${implementation.join(", ") || "N/A"}
# Generated from capabilities.jsonld

Feature: ${label}
  ${description}

${scenarios}
`;
}

/**
 * Capabilityからシナリオを生成
 */
function generateScenarios(capability: Capability, label: string, description: string): string {
	const id = capability["@id"];
	const featureName = id.replace(/Capability$/, "").replace(/([A-Z])/g, "-$1").toLowerCase().slice(1);

	// 基本的なシナリオテンプレート
	const scenarios = [
		`  Scenario: ${label} should be available
    Given the system is running
    When the "${label}" capability is invoked
    Then it should perform the expected behavior
    And the result should be successful`,

		`  Scenario: ${label} should handle errors gracefully
    Given the system is running
    When an error occurs in "${label}" capability
    Then it should handle the error appropriately
    And the error should be logged`,

		`  Scenario: ${label} should validate input
    Given the system is running
    When invalid input is provided to "${label}" capability
    Then it should reject the input
    And an appropriate error message should be returned`,
	];

	// Capabilityタイプに応じたカスタムシナリオを追加
	if (id.includes("EmailAnalysis")) {
		scenarios.push(`  Scenario: Email analysis should extract structured information
    Given an email is received
    When the email is analyzed using LLM
    Then structured information about job seekers, jobs, or agencies should be extracted
    And the extracted data should be valid`);
	}

	if (id.includes("RecordRouting")) {
		scenarios.push(`  Scenario: Record routing should create or update records
    Given extracted information is available
    When the information is routed to appropriate database records
    Then JobSeeker, Job, or Agency records should be created or updated
    And the routing should be successful`);
	}

	if (id.includes("SemanticMatching")) {
		scenarios.push(`  Scenario: Semantic matching should evaluate similarity
    Given job seeker and job data are available
    When semantic matching is performed
    Then similarity scores should be calculated
    And the scores should reflect semantic similarity`);
	}

	if (id.includes("ClerkSubscription")) {
		scenarios.push(`  Scenario: Subscription creation should store metadata
    Given a user exists in Clerk
    When a subscription is created with contract ID and amount
    Then the subscription should be stored in user metadata
    And the subscription ID should be returned`);

		scenarios.push(`  Scenario: Subscription update should modify metadata
    Given a subscription exists for a user
    When the subscription is updated with new amount or status
    Then the subscription metadata should be updated
    And the updatedAt timestamp should be set`);

		scenarios.push(`  Scenario: Subscription retrieval should return subscription data
    Given a subscription exists for a user
    When the subscription is retrieved by subscription ID
    Then the subscription data should be returned
    And the data should include status, amount, and currency`);

		scenarios.push(`  Scenario: Subscription cancellation should update status
    Given an active subscription exists for a user
    When the subscription is cancelled
    Then the subscription status should be set to "cancelled"
    And the metadata should be updated`);
	}

	return scenarios.join("\n\n");
}

/**
 * BDD featureファイルを生成
 */
function generateBDDFeatures(capabilities: CapabilitiesJSONLD, outputDir: string) {
	// 出力ディレクトリを作成
	mkdirSync(outputDir, { recursive: true });

	// 各Capabilityからfeatureファイルを生成
	for (const capability of capabilities["@graph"]) {
		if (capability["@type"] === "Capability") {
			const featureContent = generateFeatureFile(capability);
			const featureFileName = capability["@id"]
				.replace(/Capability$/, "")
				.replace(/([A-Z])/g, "-$1")
				.toLowerCase()
				.slice(1) + ".feature";

			const outputPath = join(outputDir, featureFileName);
			writeFileSync(outputPath, featureContent, "utf-8");
			console.log(`✅ Generated: ${outputPath}`);
		}
	}
}

/**
 * メイン処理
 */
function main() {
	const capabilitiesPath = join(process.cwd(), "capabilities.jsonld");
	const outputDir = join(process.cwd(), "features");

	console.log("📖 Loading capabilities.jsonld...");
	const capabilities = loadCapabilities(capabilitiesPath);

	console.log(`📦 Found ${capabilities["@graph"].length} capabilities`);
	console.log("🚀 Generating BDD feature files...");

	generateBDDFeatures(capabilities, outputDir);

	console.log(`✅ BDD feature files generated in ${outputDir}`);
}

main();





