// Coverage analysis by unit (function, component, route)
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

function analyzeCoverage() {
  const coveragePath = join(process.cwd(), 'coverage', 'coverage-summary.json');

  if (!existsSync(coveragePath)) {
    console.error('Coverage file not found. Run tests with coverage first.');
    process.exit(1);
  }

  const coverage: CoverageData = JSON.parse(readFileSync(coveragePath, 'utf-8'));

  // Group by unit type
  const functions: string[] = [];
  const components: string[] = [];
  const routes: string[] = [];
  const libs: string[] = [];
  const services: string[] = [];

  for (const [file, data] of Object.entries(coverage)) {
    if (file.includes('__tests__') || file.includes('.test.') || file.includes('.example.')) {
      continue;
    }

    if (file.includes('/api/') || file.includes('/route')) {
      routes.push(file);
    } else if (file.includes('/components/') || file.includes('.tsx')) {
      components.push(file);
    } else if (file.includes('/services/')) {
      services.push(file);
    } else if (file.includes('/lib/')) {
      libs.push(file);
    } else {
      functions.push(file);
    }
  }

  // Calculate coverage by unit
  function calculateUnitCoverage(files: string[]) {
    let totalStatements = 0;
    let coveredStatements = 0;
    let totalBranches = 0;
    let coveredBranches = 0;
    let totalFunctions = 0;
    let coveredFunctions = 0;
    let totalLines = 0;
    let coveredLines = 0;

    for (const file of files) {
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

    return {
      statements: { total: totalStatements, covered: coveredStatements, pct: totalStatements > 0 ? (coveredStatements / totalStatements) * 100 : 0 },
      branches: { total: totalBranches, covered: coveredBranches, pct: totalBranches > 0 ? (coveredBranches / totalBranches) * 100 : 0 },
      functions: { total: totalFunctions, covered: coveredFunctions, pct: totalFunctions > 0 ? (coveredFunctions / totalFunctions) * 100 : 0 },
      lines: { total: totalLines, covered: coveredLines, pct: totalLines > 0 ? (coveredLines / totalLines) * 100 : 0 },
    };
  }

  const routesCoverage = calculateUnitCoverage(routes);
  const componentsCoverage = calculateUnitCoverage(components);
  const servicesCoverage = calculateUnitCoverage(services);
  const libsCoverage = calculateUnitCoverage(libs);
  const functionsCoverage = calculateUnitCoverage(functions);

  console.log('=== Coverage by Unit Type ===\n');

  console.log('📁 Routes (API Routes):');
  console.log(`  Statements: ${routesCoverage.statements.pct.toFixed(2)}% (${routesCoverage.statements.covered}/${routesCoverage.statements.total})`);
  console.log(`  Branches: ${routesCoverage.branches.pct.toFixed(2)}% (${routesCoverage.branches.covered}/${routesCoverage.branches.total})`);
  console.log(`  Functions: ${routesCoverage.functions.pct.toFixed(2)}% (${routesCoverage.functions.covered}/${routesCoverage.functions.total})`);
  console.log(`  Lines: ${routesCoverage.lines.pct.toFixed(2)}% (${routesCoverage.lines.covered}/${routesCoverage.lines.total})`);
  console.log(`  Files: ${routes.length}\n`);

  console.log('🧩 Components:');
  console.log(`  Statements: ${componentsCoverage.statements.pct.toFixed(2)}% (${componentsCoverage.statements.covered}/${componentsCoverage.statements.total})`);
  console.log(`  Branches: ${componentsCoverage.branches.pct.toFixed(2)}% (${componentsCoverage.branches.covered}/${componentsCoverage.branches.total})`);
  console.log(`  Functions: ${componentsCoverage.functions.pct.toFixed(2)}% (${componentsCoverage.functions.covered}/${componentsCoverage.functions.total})`);
  console.log(`  Lines: ${componentsCoverage.lines.pct.toFixed(2)}% (${componentsCoverage.lines.covered}/${componentsCoverage.lines.total})`);
  console.log(`  Files: ${components.length}\n`);

  console.log('⚙️  Services:');
  console.log(`  Statements: ${servicesCoverage.statements.pct.toFixed(2)}% (${servicesCoverage.statements.covered}/${servicesCoverage.statements.total})`);
  console.log(`  Branches: ${servicesCoverage.branches.pct.toFixed(2)}% (${servicesCoverage.branches.covered}/${servicesCoverage.branches.total})`);
  console.log(`  Functions: ${servicesCoverage.functions.pct.toFixed(2)}% (${servicesCoverage.functions.covered}/${servicesCoverage.functions.total})`);
  console.log(`  Lines: ${servicesCoverage.lines.pct.toFixed(2)}% (${servicesCoverage.lines.covered}/${servicesCoverage.lines.total})`);
  console.log(`  Files: ${services.length}\n`);

  console.log('📚 Libraries/Utils:');
  console.log(`  Statements: ${libsCoverage.statements.pct.toFixed(2)}% (${libsCoverage.statements.covered}/${libsCoverage.statements.total})`);
  console.log(`  Branches: ${libsCoverage.branches.pct.toFixed(2)}% (${libsCoverage.branches.covered}/${libsCoverage.branches.total})`);
  console.log(`  Functions: ${libsCoverage.functions.pct.toFixed(2)}% (${libsCoverage.functions.covered}/${libsCoverage.functions.total})`);
  console.log(`  Lines: ${libsCoverage.lines.pct.toFixed(2)}% (${libsCoverage.lines.covered}/${libsCoverage.lines.total})`);
  console.log(`  Files: ${libs.length}\n`);

  console.log('🔧 Functions (Other):');
  console.log(`  Statements: ${functionsCoverage.statements.pct.toFixed(2)}% (${functionsCoverage.statements.covered}/${functionsCoverage.statements.total})`);
  console.log(`  Branches: ${functionsCoverage.branches.pct.toFixed(2)}% (${functionsCoverage.branches.covered}/${functionsCoverage.branches.total})`);
  console.log(`  Functions: ${functionsCoverage.functions.pct.toFixed(2)}% (${functionsCoverage.functions.covered}/${functionsCoverage.functions.total})`);
  console.log(`  Lines: ${functionsCoverage.lines.pct.toFixed(2)}% (${functionsCoverage.lines.covered}/${functionsCoverage.lines.total})`);
  console.log(`  Files: ${functions.length}\n`);

  // Overall coverage
  const allFiles = [...routes, ...components, ...services, ...libs, ...functions];
  const overallCoverage = calculateUnitCoverage(allFiles);

  console.log('📊 Overall Coverage:');
  console.log(`  Statements: ${overallCoverage.statements.pct.toFixed(2)}% (${overallCoverage.statements.covered}/${overallCoverage.statements.total})`);
  console.log(`  Branches: ${overallCoverage.branches.pct.toFixed(2)}% (${overallCoverage.branches.covered}/${overallCoverage.branches.total})`);
  console.log(`  Functions: ${overallCoverage.functions.pct.toFixed(2)}% (${overallCoverage.functions.covered}/${overallCoverage.functions.total})`);
  console.log(`  Lines: ${overallCoverage.lines.pct.toFixed(2)}% (${overallCoverage.lines.covered}/${overallCoverage.lines.total})`);
  console.log(`  Total Files: ${allFiles.length}`);
}

analyzeCoverage();
