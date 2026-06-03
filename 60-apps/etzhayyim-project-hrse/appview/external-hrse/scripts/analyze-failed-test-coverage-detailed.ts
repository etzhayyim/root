// Detailed analysis of failed test coverage
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

interface CoverageData {
  [file: string]: {
    statements: { total: number; covered: number; pct: number };
    branches: { total: number; covered: number; pct: number };
    functions: { total: number; covered: number; pct: number };
    lines: { total: number; covered: number; pct: number };
  };
}

// Failed test files and their related source files
const failedTestMapping: Record<string, string[]> = {
  'src/__tests__/lib/clerk-subscription.complete.test.ts': [
    'src/lib/clerk-subscription.ts',
  ],
  'src/__tests__/api/webhooks/clerk/route.complete.test.ts': [
    'src/app/api/webhooks/clerk/route.ts',
  ],
  'src/__tests__/api/webhooks/resend.test.ts': [
    'src/app/api/webhooks/resend/route.ts',
  ],
  'src/__tests__/graphql/integration.test.ts': [
    'src/app/api/graphql/route.ts',
  ],
  'src/__tests__/pages/freelancer/jobs.test.tsx': [
    'src/app/freelancer/jobs/page.tsx',
  ],
  'src/__tests__/pages/freelancer/profile.test.tsx': [
    'src/app/freelancer/profile/page.tsx',
  ],
};

function analyzeFailedTestCoverage() {
  const coveragePath = join(process.cwd(), 'coverage', 'coverage-summary.json');

  if (!existsSync(coveragePath)) {
    console.error('Coverage file not found. Run tests with coverage first.');
    return;
  }

  const coverage: CoverageData = JSON.parse(readFileSync(coveragePath, 'utf-8'));

  console.log('=== Failed Tests Coverage Analysis (TDD Perspective) ===\n');

  for (const [testFile, sourceFiles] of Object.entries(failedTestMapping)) {
    console.log(`📄 ${testFile}:`);

    for (const sourceFile of sourceFiles) {
      const data = coverage[sourceFile];
      if (data) {
        console.log(`\n  ${sourceFile}:`);
        console.log(`    Statements: ${data.statements.pct.toFixed(2)}% (${data.statements.covered}/${data.statements.total})`);
        console.log(`    Branches: ${data.branches.pct.toFixed(2)}% (${data.branches.covered}/${data.branches.total})`);
        console.log(`    Functions: ${data.functions.pct.toFixed(2)}% (${data.functions.covered}/${data.functions.total})`);
        console.log(`    Lines: ${data.lines.pct.toFixed(2)}% (${data.lines.covered}/${data.lines.total})`);

        // Identify uncovered areas
        if (data.statements.pct < 100) {
          console.log(`    ⚠️  Low coverage: ${(100 - data.statements.pct).toFixed(2)}% statements uncovered`);
        }
      } else {
        console.log(`\n  ${sourceFile}: No coverage data (0% coverage)`);
      }
    }
    console.log('');
  }

  // Calculate average coverage for failed test areas
  const allFailedSourceFiles = Object.values(failedTestMapping).flat();
  const uniqueFiles = [...new Set(allFailedSourceFiles)];

  let totalStatements = 0;
  let coveredStatements = 0;
  let totalBranches = 0;
  let coveredBranches = 0;
  let totalFunctions = 0;
  let coveredFunctions = 0;
  let totalLines = 0;
  let coveredLines = 0;

  for (const file of uniqueFiles) {
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

  if (totalStatements > 0) {
    console.log('=== Average Coverage for Failed Test Areas ===');
    console.log(`Statements: ${(coveredStatements / totalStatements * 100).toFixed(2)}%`);
    console.log(`Branches: ${(coveredBranches / totalBranches * 100).toFixed(2)}%`);
    console.log(`Functions: ${(coveredFunctions / totalFunctions * 100).toFixed(2)}%`);
    console.log(`Lines: ${(coveredLines / totalLines * 100).toFixed(2)}%`);
  }
}

analyzeFailedTestCoverage();
