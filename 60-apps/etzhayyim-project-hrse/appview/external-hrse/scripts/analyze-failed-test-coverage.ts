// Analyze coverage for failed tests
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

interface CoverageData {
  [file: string]: {
    statements: { total: number; covered: number; pct: number };
    branches: { total: number; covered: number; pct: number };
    functions: { total: number; covered: number; pct: number };
    lines: { total: number; covered: number; pct: number };
  };
}

function analyzeFailedTestCoverage() {
  // Get failed tests
  const testOutput = execSync('pnpm vitest --run 2>&1', { encoding: 'utf-8' });
  const failedTests: string[] = [];

  const lines = testOutput.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('FAIL')) {
      const match = lines[i].match(/FAIL\s+(.+?)\s+/);
      if (match) {
        failedTests.push(match[1]);
      }
    }
  }

  console.log('=== Failed Tests Coverage Analysis ===\n');
  console.log(`Total Failed Tests: ${failedTests.length}\n`);

  if (failedTests.length === 0) {
    console.log('No failed tests found.');
    return;
  }

  // Load coverage data
  const coveragePath = join(process.cwd(), 'coverage', 'coverage-summary.json');
  if (!existsSync(coveragePath)) {
    console.error('Coverage file not found. Run tests with coverage first.');
    return;
  }

  const coverage: CoverageData = JSON.parse(readFileSync(coveragePath, 'utf-8'));

  // Analyze coverage for files related to failed tests
  const affectedFiles = new Set<string>();

  for (const test of failedTests) {
    // Extract file path from test name
    const testFile = test.split('>')[0].trim();
    const sourceFile = testFile
      .replace('src/__tests__/', 'src/')
      .replace('.test.ts', '.ts')
      .replace('.complete.test.ts', '.ts')
      .replace('/__tests__/', '/');

    // Find related source files
    for (const [file, data] of Object.entries(coverage)) {
      if (file.includes(sourceFile) || sourceFile.includes(file)) {
        affectedFiles.add(file);
      }
    }
  }

  console.log('Affected Source Files:');
  for (const file of Array.from(affectedFiles).sort()) {
    const data = coverage[file];
    if (data) {
      console.log(`\n${file}:`);
      console.log(`  Statements: ${data.statements.pct.toFixed(2)}% (${data.statements.covered}/${data.statements.total})`);
      console.log(`  Branches: ${data.branches.pct.toFixed(2)}% (${data.branches.covered}/${data.branches.total})`);
      console.log(`  Functions: ${data.functions.pct.toFixed(2)}% (${data.functions.covered}/${data.functions.total})`);
      console.log(`  Lines: ${data.lines.pct.toFixed(2)}% (${data.lines.covered}/${data.lines.total})`);
    }
  }

  // Calculate average coverage for failed test areas
  if (affectedFiles.size > 0) {
    let totalStatements = 0;
    let coveredStatements = 0;
    let totalBranches = 0;
    let coveredBranches = 0;
    let totalFunctions = 0;
    let coveredFunctions = 0;
    let totalLines = 0;
    let coveredLines = 0;

    for (const file of affectedFiles) {
      const data = coverage[file];
      if (data) {
        totalStatements += data.statements.total;
        coveredStatements += data.statements.covered;
        totalBranches += data.branches.total;
        coveredBranches += data.branches.covered;
        totalFunctions += data.functions.total;
        coveredFunctions += data.functions.covered;
        totalLines += data.lines.total;
        coveredLines += data.lines.covered;
      }
    }

    console.log('\n=== Average Coverage for Failed Test Areas ===');
    console.log(`Statements: ${(coveredStatements / totalStatements * 100).toFixed(2)}%`);
    console.log(`Branches: ${(coveredBranches / totalBranches * 100).toFixed(2)}%`);
    console.log(`Functions: ${(coveredFunctions / totalFunctions * 100).toFixed(2)}%`);
    console.log(`Lines: ${(coveredLines / totalLines * 100).toFixed(2)}%`);
  }
}

analyzeFailedTestCoverage();
