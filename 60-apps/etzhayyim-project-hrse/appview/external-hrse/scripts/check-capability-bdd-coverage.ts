// @etzhayyim/cyber-freelance#CapabilityBDDCoverageChecker
// capabilityからBDDへの対応状況をカバレッジで確認

import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { glob } from "glob";

interface Capability {
	"@id": string;
	"@type": string;
	"rdfs:label": Array<{ "@value": string; "@language": string }>;
	"dcterms:description": Array<{ "@value": string; "@language": string }>;
	implementation?: string[];
}

interface CapabilitiesJSONLD {
	"@context": Record<string, string>;
	"@graph": Capability[];
}

interface FeatureFile {
	capabilityId: string;
	featurePath: string;
	scenarios: number;
	steps: number;
}

interface StepDefinition {
	file: string;
	steps: string[];
}

/**
 * capabilities.jsonldを読み込む
 */
function loadCapabilities(filePath: string): CapabilitiesJSONLD {
	const content = readFileSync(filePath, "utf-8");
	return JSON.parse(content) as CapabilitiesJSONLD;
}

/**
 * Featureファイルを解析
 */
function parseFeatureFile(filePath: string): FeatureFile {
	const content = readFileSync(filePath, "utf-8");
	const capabilityId = content.match(/# @etzhayyim\/cyber-freelance#(\w+)/)?.[1] || "";
	const scenarios = (content.match(/Scenario:/g) || []).length;
	const steps = (content.match(/(Given|When|Then|And)/g) || []).length;

	return {
		capabilityId,
		featurePath: filePath,
		scenarios,
		steps,
	};
}

/**
 * Step定義ファイルを解析
 */
function parseStepDefinitions(dir: string): StepDefinition[] {
	const stepFiles = glob.sync(join(dir, "**/*.steps.ts"));
	const definitions: StepDefinition[] = [];

	for (const file of stepFiles) {
		const content = readFileSync(file, "utf-8");
		const stepMatches = content.matchAll(/(Given|When|Then|And)\s*\(["']([^"']+)["']/g);
		const steps: string[] = [];

		for (const match of stepMatches) {
			steps.push(match[2]);
		}

		definitions.push({
			file,
			steps,
		});
	}

	return definitions;
}

/**
 * 実装ファイルの存在確認
 */
function checkImplementationFiles(implementation: string[]): {
	exists: number;
	total: number;
	files: Array<{ path: string; exists: boolean }>;
} {
	const files = implementation.map((path) => ({
		path,
		exists: existsSync(join(process.cwd(), path)),
	}));

	return {
		exists: files.filter((f) => f.exists).length,
		total: files.length,
		files,
	};
}

/**
 * カバレッジレポートを読み込む（c8/nyc形式）
 */
function loadCoverageReport(): Record<string, any> | null {
	// c8/nycのカバレッジファイルを探す
	const coveragePaths = [
		join(process.cwd(), "coverage", "coverage-final.json"),
		join(process.cwd(), ".nycOutput", "coverage-final.json"),
		join(process.cwd(), ".c8_output", "coverage-final.json"),
	];

	for (const coveragePath of coveragePaths) {
		if (existsSync(coveragePath)) {
			const content = readFileSync(coveragePath, "utf-8");
			return JSON.parse(content);
		}
	}

	return null;
}

/**
 * カバレッジサマリーを読み込む（c8/nyc形式）
 */
function loadCoverageSummary(): {
	lines: { total: number; covered: number; pct: number };
	functions: { total: number; covered: number; pct: number };
	branches: { total: number; covered: number; pct: number };
	statements: { total: number; covered: number; pct: number };
} | null {
	const summaryPath = join(process.cwd(), "coverage", "coverage-summary.json");
	if (!existsSync(summaryPath)) {
		return null;
	}

	const content = readFileSync(summaryPath, "utf-8");
	const summary = JSON.parse(content);

	// 全体のサマリーを取得（totalキーがある場合）
	if (summary.total) {
		return summary.total;
	}

	// 各ファイルのカバレッジから全体を計算
	const files = Object.values(summary).filter((item: any) => item.lines) as Array<{
		lines: { total: number; covered: number; pct: number };
		functions: { total: number; covered: number; pct: number };
		branches: { total: number; covered: number; pct: number };
		statements: { total: number; covered: number; pct: number };
	}>;

	if (files.length === 0) {
		return null;
	}

	return {
		lines: {
			total: files.reduce((sum, f) => sum + f.lines.total, 0),
			covered: files.reduce((sum, f) => sum + f.lines.covered, 0),
			pct: 0,
		},
		functions: {
			total: files.reduce((sum, f) => sum + f.functions.total, 0),
			covered: files.reduce((sum, f) => sum + f.functions.covered, 0),
			pct: 0,
		},
		branches: {
			total: files.reduce((sum, f) => sum + f.branches.total, 0),
			covered: files.reduce((sum, f) => sum + f.branches.covered, 0),
			pct: 0,
		},
		statements: {
			total: files.reduce((sum, f) => sum + f.statements.total, 0),
			covered: files.reduce((sum, f) => sum + f.statements.covered, 0),
			pct: 0,
		},
	};
}

/**
 * ファイルのカバレッジを取得
 */
function getFileCoverage(
	coverage: Record<string, any> | null,
	filePath: string,
): {
	statements: number;
	branches: number;
	functions: number;
	lines: number;
} | null {
	if (!coverage) {
		return null;
	}

	const normalizedPath = filePath.replace(process.cwd() + "/", "");
	const coverageData = Object.values(coverage).find((data: any) => data.path === normalizedPath) as any;

	if (!coverageData) {
		return null;
	}

	const statements = Object.keys(coverageData.statementMap).length;
	const coveredStatements = Object.values(coverageData.s).filter((v: any) => v > 0).length;
	const statementCoverage = statements > 0 ? (coveredStatements / statements) * 100 : 0;

	const branches = Object.keys(coverageData.branchMap).length;
	const coveredBranches = Object.values(coverageData.b).flat().filter((v: any) => v > 0).length;
	const branchCoverage = branches > 0 ? (coveredBranches / branches) * 100 : 0;

	const functions = Object.keys(coverageData.fnMap).length;
	const coveredFunctions = Object.values(coverageData.f).filter((v: any) => v > 0).length;
	const functionCoverage = functions > 0 ? (coveredFunctions / functions) * 100 : 0;

	const lines = Object.keys(coverageData.statementMap).length;
	const coveredLines = Object.values(coverageData.s).filter((v: any) => v > 0).length;
	const lineCoverage = lines > 0 ? (coveredLines / lines) * 100 : 0;

	return {
		statements: statementCoverage,
		branches: branchCoverage,
		functions: functionCoverage,
		lines: lineCoverage,
	};
}

/**
 * メイン処理
 */
function main() {
	console.log("📊 Capability to BDD Coverage Report\n");

	const capabilitiesPath = join(process.cwd(), "capabilities.jsonld");
	const featuresDir = join(process.cwd(), "features");
	const stepDefinitionsDir = join(featuresDir, "stepDefinitions");

	// capabilities.jsonldを読み込む
	const capabilities = loadCapabilities(capabilitiesPath);
	const capabilityMap = new Map<string, Capability>();

	for (const capability of capabilities["@graph"]) {
		if (capability["@type"] === "Capability") {
			capabilityMap.set(capability["@id"], capability);
		}
	}

	// Featureファイルを読み込む
	const featureFiles = glob.sync(join(featuresDir, "*.feature"));
	const featureMap = new Map<string, FeatureFile>();

	for (const file of featureFiles) {
		const feature = parseFeatureFile(file);
		if (feature.capabilityId) {
			featureMap.set(feature.capabilityId, feature);
		}
	}

	// Step定義を読み込む
	const stepDefinitions = parseStepDefinitions(stepDefinitionsDir);

	// カバレッジレポートを読み込む
	const coverage = loadCoverageReport();
	const coverageSummary = loadCoverageSummary();

	// レポートを生成
	console.log("=".repeat(100));
	console.log("Capability to BDD Coverage Report");
	console.log("=".repeat(100));
	console.log();

	// 全体のカバレッジサマリーを表示
	if (coverageSummary) {
		console.log("📈 Overall Coverage Summary");
		console.log("-".repeat(100));
		console.log(`Lines:      ${coverageSummary.lines.covered}/${coverageSummary.lines.total} (${coverageSummary.lines.pct.toFixed(1)}%)`);
		console.log(`Functions:  ${coverageSummary.functions.covered}/${coverageSummary.functions.total} (${coverageSummary.functions.pct.toFixed(1)}%)`);
		console.log(`Branches:   ${coverageSummary.branches.covered}/${coverageSummary.branches.total} (${coverageSummary.branches.pct.toFixed(1)}%)`);
		console.log(`Statements: ${coverageSummary.statements.covered}/${coverageSummary.statements.total} (${coverageSummary.statements.pct.toFixed(1)}%)`);
		console.log();
	} else if (coverage) {
		console.log("⚠️  Coverage summary not found, but coverage data exists");
		console.log("   Run 'pnpm test:bdd:coverage:report' to generate summary");
		console.log();
	} else {
		console.log("⚠️  No coverage data found");
		console.log("   Run BDD tests with coverage: 'pnpm test:bdd:coverage' or 'pnpm test:e2e:bdd:coverage'");
		console.log();
	}

	let totalCapabilities = 0;
	let coveredCapabilities = 0;
	let totalScenarios = 0;
	let totalSteps = 0;
	let totalImplementationFiles = 0;
	let coveredImplementationFiles = 0;
	let capabilitiesWithLowCoverage: Array<{
		capabilityId: string;
		label: string;
		avgCoverage: number;
	}> = [];

	for (const [capabilityId, capability] of capabilityMap.entries()) {
		totalCapabilities++;
		const label = capability["rdfs:label"]?.find((l) => l["@language"] === "en")?.["@value"] || capabilityId;
		const feature = featureMap.get(capabilityId);
		const implementation = checkImplementationFiles(capability.implementation || []);

		totalImplementationFiles += implementation.total;
		coveredImplementationFiles += implementation.exists;

		if (feature) {
			coveredCapabilities++;
			totalScenarios += feature.scenarios;
			totalSteps += feature.steps;

			console.log(`✅ ${label} (${capabilityId})`);
			console.log(`   Feature: ${feature.featurePath}`);
			console.log(`   Scenarios: ${feature.scenarios}`);
			console.log(`   Steps: ${feature.steps}`);
			console.log(`   Implementation Files: ${implementation.exists}/${implementation.total}`);

			// カバレッジ情報を表示
			if (coverage && capability.implementation) {
				const coverageValues: number[] = [];
				for (const implFile of capability.implementation) {
					const fileCoverage = getFileCoverage(coverage, implFile);
					if (fileCoverage) {
						const avgCoverage = (fileCoverage.statements + fileCoverage.branches + fileCoverage.functions + fileCoverage.lines) / 4;
						coverageValues.push(avgCoverage);

						const coverageIcon = avgCoverage >= 80 ? "✅" : avgCoverage >= 50 ? "⚠️" : "❌";
						console.log(`   ${coverageIcon} Coverage for ${implFile}:`);
						console.log(`     Statements: ${fileCoverage.statements.toFixed(1)}%`);
						console.log(`     Branches: ${fileCoverage.branches.toFixed(1)}%`);
						console.log(`     Functions: ${fileCoverage.functions.toFixed(1)}%`);
						console.log(`     Lines: ${fileCoverage.lines.toFixed(1)}%`);
						console.log(`     Average: ${avgCoverage.toFixed(1)}%`);
					} else {
						console.log(`   ⚠️  Coverage data not found for ${implFile}`);
					}
				}

				// 平均カバレッジが低いcapabilityを記録
				if (coverageValues.length > 0) {
					const avgCoverage = coverageValues.reduce((a, b) => a + b, 0) / coverageValues.length;
					if (avgCoverage < 80) {
						capabilitiesWithLowCoverage.push({
							capabilityId,
							label,
							avgCoverage,
						});
					}
				}
			}
		} else {
			console.log(`❌ ${label} (${capabilityId})`);
			console.log(`   Feature: Not generated`);
			console.log(`   Implementation Files: ${implementation.exists}/${implementation.total}`);
		}

		console.log();
	}

	// サマリー
	console.log("=".repeat(100));
	console.log("Summary");
	console.log("=".repeat(100));
	console.log(`Total Capabilities: ${totalCapabilities}`);
	console.log(`Covered Capabilities: ${coveredCapabilities} (${((coveredCapabilities / totalCapabilities) * 100).toFixed(1)}%)`);
	console.log(`Total Scenarios: ${totalScenarios}`);
	console.log(`Total Steps: ${totalSteps}`);
	console.log(`Implementation Files: ${coveredImplementationFiles}/${totalImplementationFiles} (${((coveredImplementationFiles / totalImplementationFiles) * 100).toFixed(1)}%)`);
	console.log(`Step Definitions: ${stepDefinitions.length} files, ${stepDefinitions.reduce((sum, def) => sum + def.steps.length, 0)} steps`);
	console.log();

	// カバレッジが低いcapabilityを警告
	if (capabilitiesWithLowCoverage.length > 0) {
		console.log("=".repeat(100));
		console.log("⚠️  Capabilities with Low Coverage (< 80%)");
		console.log("=".repeat(100));
		for (const cap of capabilitiesWithLowCoverage) {
			console.log(`❌ ${cap.label} (${cap.capabilityId}): ${cap.avgCoverage.toFixed(1)}%`);
		}
		console.log();
	}

	// カバレッジレポートの場所を表示
	if (coverage || coverageSummary) {
		const htmlReportPath = join(process.cwd(), "coverage", "index.html");
		if (existsSync(htmlReportPath)) {
			console.log("📊 HTML Coverage Report:");
			console.log(`   ${htmlReportPath}`);
			console.log(`   Open with: open ${htmlReportPath}`);
			console.log();
		}
	}

	// 終了コードを設定（カバレッジが低い場合）
	if (capabilitiesWithLowCoverage.length > 0) {
		process.exit(1);
	}
}

main();




