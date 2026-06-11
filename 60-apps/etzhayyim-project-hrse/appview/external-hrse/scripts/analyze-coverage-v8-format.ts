// Analyze v8 coverage format
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

interface V8CoverageData {
  [file: string]: {
    s: { [statementId: number]: number }; // statements
    b: { [branchId: number]: number[] }; // branches
    f: { [functionId: number]: number }; // functions
  };
}

function analyzeV8Coverage() {
  const coveragePath = join(process.cwd(), 'coverage', 'coverage-final.json');

  if (!existsSync(coveragePath)) {
    console.error('Coverage file not found.');
    return;
  }

  const coverage: V8CoverageData = JSON.parse(readFileSync(coveragePath, 'utf-8'));

  // Group by unit type
  const routes: Array<{ file: string; data: any }> = [];
  const components: Array<{ file: string; data: any }> = [];
  const services: Array<{ file: string; data: any }> = [];
  const libs: Array<{ file: string; data: any }> = [];
  const other: Array<{ file: string; data: any }> = [];

  for (const [file, data] of Object.entries(coverage)) {
    if (file.includes('__tests__') || file.includes('.test.') || file.includes('.example.')) {
      continue;
    }

    // Calculate coverage percentages
    const statements = Object.values(data.s || {});
    const branches = Object.values(data.b || {}).flat();
    const functions = Object.values(data.f || {});

    const statementsCovered = statements.filter((v: number) => v > 0).length;
    const branchesCovered = branches.filter((v: number) => v > 0).length;
    const functionsCovered = functions.filter((v: number) => v > 0).length;

    const coverageData = {
      statements: {
        total: statements.length,
        covered: statementsCovered,
        pct: statements.length > 0 ? (statementsCovered / statements.length) * 100 : 0,
      },
      branches: {
        total: branches.length,
        covered: branchesCovered,
        pct: branches.length > 0 ? (branchesCovered / branches.length) * 100 : 0,
      },
      functions: {
        total: functions.length,
        covered: functionsCovered,
        pct: functions.length > 0 ? (functionsCovered / functions.length) * 100 : 0,
      },
      lines: {
        total: statements.length, // Approximate
        covered: statementsCovered,
        pct: statements.length > 0 ? (statementsCovered / statements.length) * 100 : 0,
      },
    };

    if (file.includes('/api/') || file.includes('/route')) {
      routes.push({ file, data: coverageData });
    } else if (file.includes('/components/') || file.endsWith('.tsx')) {
      components.push({ file, data: coverageData });
    } else if (file.includes('/services/')) {
      services.push({ file, data: coverageData });
    } else if (file.includes('/lib/')) {
      libs.push({ file, data: coverageData });
    } else {
      other.push({ file, data: coverageData });
    }
  }

  // Calculate coverage by unit
  function calculateUnitCoverage(items: Array<{ file: string; data: any }>) {
    let totalStatements = 0;
    let coveredStatements = 0;
    let totalBranches = 0;
    let coveredBranches = 0;
    let totalFunctions = 0;
    let coveredFunctions = 0;
    let totalLines = 0;
    let coveredLines = 0;

    for (const { data } of items) {
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
  const otherCoverage = calculateUnitCoverage(other);

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
  console.log(`  Statements: ${otherCoverage.statements.pct.toFixed(2)}% (${otherCoverage.statements.covered}/${otherCoverage.statements.total})`);
  console.log(`  Branches: ${otherCoverage.branches.pct.toFixed(2)}% (${otherCoverage.branches.covered}/${otherCoverage.branches.total})`);
  console.log(`  Functions: ${otherCoverage.functions.pct.toFixed(2)}% (${otherCoverage.functions.covered}/${otherCoverage.functions.total})`);
  console.log(`  Lines: ${otherCoverage.lines.pct.toFixed(2)}% (${otherCoverage.lines.covered}/${otherCoverage.lines.total})`);
  console.log(`  Files: ${other.length}\n`);

  // Overall coverage
  const allFiles = [...routes, ...components, ...services, ...libs, ...other];
  const overallCoverage = calculateUnitCoverage(allFiles);

  console.log('📊 Overall Coverage:');
  console.log(`  Statements: ${overallCoverage.statements.pct.toFixed(2)}% (${overallCoverage.statements.covered}/${overallCoverage.statements.total})`);
  console.log(`  Branches: ${overallCoverage.branches.pct.toFixed(2)}% (${overallCoverage.branches.covered}/${overallCoverage.branches.total})`);
  console.log(`  Functions: ${overallCoverage.functions.pct.toFixed(2)}% (${overallCoverage.functions.covered}/${overallCoverage.functions.total})`);
  console.log(`  Lines: ${overallCoverage.lines.pct.toFixed(2)}% (${overallCoverage.lines.covered}/${overallCoverage.lines.total})`);
  console.log(`  Total Files: ${allFiles.length}\n`);

  // File-level details
  console.log('=== File-Level Coverage Details ===\n');

  for (const { file, data } of allFiles.slice(0, 20)) {
    console.log(`${file}:`);
    console.log(`  Statements: ${data.statements.pct.toFixed(2)}% (${data.statements.covered}/${data.statements.total})`);
    console.log(`  Branches: ${data.branches.pct.toFixed(2)}% (${data.branches.covered}/${data.branches.total})`);
    console.log(`  Functions: ${data.functions.pct.toFixed(2)}% (${data.functions.covered}/${data.functions.total})`);
    console.log(`  Lines: ${data.lines.pct.toFixed(2)}% (${data.lines.covered}/${data.lines.total})`);
    console.log('');
  }
}

analyzeV8Coverage();
