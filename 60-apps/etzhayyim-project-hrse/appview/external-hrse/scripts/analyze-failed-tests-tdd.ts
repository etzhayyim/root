// Analyze failed tests from TDD perspective
import { execSync } from 'child_process';

function analyzeFailedTests() {
  try {
    const testOutput = execSync('pnpm vitest --run 2>&1', { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });

    const failedTests: Array<{ testFile: string; testName: string; error: string }> = [];
    const lines = testOutput.split('\n');

    let currentTestFile = '';
    let currentTestName = '';
    let collectingError = false;
    let errorLines: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Detect failed test file
      if (line.includes('FAIL') && line.includes('.test.')) {
        const match = line.match(/FAIL\s+(.+?)\s+\[/);
        if (match) {
          currentTestFile = match[1];
        }
      }

      // Detect test name
      if (line.includes('×') && currentTestFile) {
        const match = line.match(/×\s+(.+?)$/);
        if (match) {
          if (currentTestName && errorLines.length > 0) {
            failedTests.push({
              testFile: currentTestFile,
              testName: currentTestName,
              error: errorLines.join('\n'),
            });
          }
          currentTestName = match[1].trim();
          errorLines = [];
          collectingError = true;
        }
      }

      // Collect error details
      if (collectingError && (line.includes('Error:') || line.includes('AssertionError:') || line.includes('TypeError:'))) {
        errorLines.push(line.trim());
        collectingError = false;
      }

      if (errorLines.length > 0 && line.trim() && !line.includes('at ') && !line.includes('❯')) {
        if (line.trim().length < 200) {
          errorLines.push(line.trim());
        }
      }
    }

    // Add last test if exists
    if (currentTestName && errorLines.length > 0) {
      failedTests.push({
        testFile: currentTestFile,
        testName: currentTestName,
        error: errorLines.join('\n'),
      });
    }

    console.log('=== Failed Tests Analysis (TDD Perspective) ===\n');
    console.log(`Total Failed Tests: ${failedTests.length}\n`);

    // Group by test file
    const byFile: Record<string, Array<{ testName: string; error: string }>> = {};
    for (const test of failedTests) {
      if (!byFile[test.testFile]) {
        byFile[test.testFile] = [];
      }
      byFile[test.testFile].push({ testName: test.testName, error: test.error });
    }

    console.log('=== Failed Tests by File ===\n');
    for (const [file, tests] of Object.entries(byFile)) {
      console.log(`📄 ${file}:`);
      console.log(`   Failed Tests: ${tests.length}\n`);

      for (const test of tests) {
        console.log(`   ❌ ${test.testName}`);
        const errorPreview = test.error.split('\n')[0];
        if (errorPreview) {
          console.log(`      Error: ${errorPreview.substring(0, 100)}...`);
        }
      }
      console.log('');
    }

    // Categorize failures
    const categories = {
      'Mock/Setup Issues': [] as string[],
      'API/Route Issues': [] as string[],
      'Component Issues': [] as string[],
      'Integration Issues': [] as string[],
      'Other': [] as string[],
    };

    for (const test of failedTests) {
      const error = test.error.toLowerCase();
      if (error.includes('mock') || error.includes('vi.fn') || error.includes('constructor')) {
        categories['Mock/Setup Issues'].push(`${test.testFile} > ${test.testName}`);
      } else if (test.testFile.includes('/api/') || test.testFile.includes('/route')) {
        categories['API/Route Issues'].push(`${test.testFile} > ${test.testName}`);
      } else if (test.testFile.includes('/pages/') || test.testFile.includes('/components/')) {
        categories['Component Issues'].push(`${test.testFile} > ${test.testName}`);
      } else if (test.testFile.includes('integration')) {
        categories['Integration Issues'].push(`${test.testFile} > ${test.testName}`);
      } else {
        categories['Other'].push(`${test.testFile} > ${test.testName}`);
      }
    }

    console.log('=== Failure Categories ===\n');
    for (const [category, tests] of Object.entries(categories)) {
      if (tests.length > 0) {
        console.log(`${category}: ${tests.length} tests`);
        tests.slice(0, 5).forEach(test => console.log(`  - ${test}`));
        if (tests.length > 5) {
          console.log(`  ... and ${tests.length - 5} more`);
        }
        console.log('');
      }
    }

    return failedTests;
  } catch (error: any) {
    console.error('Error analyzing tests:', error.message);
    return [];
  }
}

analyzeFailedTests();
