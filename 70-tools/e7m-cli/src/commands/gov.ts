import { Command } from 'commander';
import { computeGovCoverageScore, saveGovCoverageSnapshot, saveGovCoverageMarkdown } from '../lib/gov-coverage.js';

export const govCmd = new Command('gov').description('Manage government coverage and maturity scoring');

govCmd
  .command('coverage-score')
  .description('Display current government coverage maturity score')
  .action(async () => {
    try {
      const score = await computeGovCoverageScore();

      console.log('\n┌─ Government Coverage Maturity Score ─────────────────────┐');
      console.log(`│ Overall: ${score.total}/100${' '.repeat(48 - score.total.toString().length)}│`);
      console.log('├──────────────────────────────────────────────────────────┤');

      const entries = [
        score.breakdown.l1,
        score.breakdown.l2,
        score.breakdown.l3,
        score.breakdown.l4,
        score.breakdown.l5,
      ];

      for (const entry of entries) {
        const bar = '█'.repeat(Math.floor(entry.value / 5)) + '░'.repeat(20 - Math.floor(entry.value / 5));
        const padding = ' '.repeat(Math.max(0, 25 - entry.label.length));
        console.log(`│ ${entry.label}${padding}│ ${bar} ${entry.value}% │`);
      }

      console.log('├──────────────────────────────────────────────────────────┤');

      if (score.gaps.length > 0) {
        console.log('│ Coverage Gaps:                                           │');
        for (const gap of score.gaps) {
          const lines = gap.match(/.{1,50}/g) || [];
          for (let i = 0; i < lines.length; i++) {
            const prefix = i === 0 ? '│ ◦ ' : '│   ';
            console.log(`${prefix}${lines[i]}${' '.repeat(Math.max(0, 54 - lines[i].length))}│`);
          }
        }
      } else {
        console.log('│ ✓ No critical coverage gaps                             │');
      }

      console.log('└──────────────────────────────────────────────────────────┘');
      console.log(`\nSnapshot: ${score.timestamp}`);
    } catch (err) {
      console.error('Failed to compute coverage score:', err);
      process.exit(1);
    }
  });

govCmd
  .command('coverage-audit')
  .description('Run audit and save snapshot reports (JSON + Markdown)')
  .action(async () => {
    try {
      const score = await computeGovCoverageScore();

      const jsonPath = await saveGovCoverageSnapshot(score);
      const mdPath = await saveGovCoverageMarkdown(score);

      console.log(`\n✓ Coverage audit complete`);
      console.log(`  JSON snapshot: ${jsonPath}`);
      console.log(`  Markdown report: ${mdPath}`);
      console.log(`\nScore: ${score.total}/100\n`);
    } catch (err) {
      console.error('Coverage audit failed:', err);
      process.exit(1);
    }
  });

govCmd
  .command('coverage-plan')
  .option('--target <score>', 'Target coverage score (default: 85)', '85')
  .description('Generate improvement plan to reach target coverage')
  .action(async (options: { target: string }) => {
    try {
      const score = await computeGovCoverageScore();
      const target = parseInt(options.target, 10);

      if (isNaN(target) || target < 0 || target > 100) {
        console.error('Invalid target score (must be 0-100)');
        process.exit(1);
      }

      const gap = target - score.total;

      console.log('\n┌─ Government Coverage Improvement Plan ───────────────────┐');
      console.log(`│ Current: ${score.total}/100  Target: ${target}/100  Gap: ${gap > 0 ? '+' : ''}${gap.toFixed(1)}${' '.repeat(27 - gap.toFixed(1).length)}│`);
      console.log('├──────────────────────────────────────────────────────────┤');

      const priorities: Array<{
        layer: string;
        current: number;
        potential: number;
        adr: string;
        tasks: string[];
      }> = [
        {
          layer: 'L1 ISO-3 Completeness',
          current: score.breakdown.l1.value,
          potential: 20,
          adr: 'ADR-2605242330',
          tasks: [
            'Complete remaining 20 ISO-3 country BPMN namespace entries',
            'Validate jurisdiction coverage against UN member roster',
          ],
        },
        {
          layer: 'L2 COFOG×country Density',
          current: score.breakdown.l2.value,
          potential: 25,
          adr: 'ADR-2605242330',
          tasks: [
            'Add 50+ BPMN process definitions across COFOG categories',
            'Extend from 4 major categories to 7 (add Healthcare, Housing, Environment)',
            'Contribute to 00-contracts/bpmn/com/etzhayyim/gov<ISO3>/ with jurisdiction-specific processes',
          ],
        },
        {
          layer: 'L3 substrate-port Coverage',
          current: score.breakdown.l3.value,
          potential: 20,
          adr: 'ADR-2605214000',
          tasks: [
            'Verify all 3 L3 apps are kotoba (govern-mcp-component, lawfirm-admin, legal-entity)',
            'Run integration test suite against etzhayyim.com edge (no legacy residue)',
            'Stage PR with @etzhayyim/ package rename (post-bootstrap Council)',
          ],
        },
        {
          layer: 'L4 Ingest Records',
          current: score.breakdown.l4.value,
          potential: 20,
          adr: 'ADR-2605242330',
          tasks: [
            'Expand 70-tools/scripts/gov/ from 3 scripts to 6-8 (add jurisdiction-specific processors)',
            'Target: 1000 demonstrator records (currently ~421)',
            'Emit to com.etzhayyim.gov.agency with full BPMN linkage',
          ],
        },
        {
          layer: 'L5 Cell Activation',
          current: score.breakdown.l5.value,
          potential: 15,
          adr: 'ADR-2605250100/200/300',
          tasks: [
            'Await Council attestation (post-bootstrap 2026-06-19)',
            'Activate member_registry, religious_marriage, religious_corp_taxation cells',
            'Remove import-time RuntimeError gates when Council Lv6+ supermajority attests',
          ],
        },
      ];

      // Sort by potential impact descending
      priorities.sort((a, b) => (b.potential * (100 - b.current)) - (a.potential * (100 - a.current)));

      for (let i = 0; i < priorities.length; i++) {
        const p = priorities[i];
        const impactPoints = Math.round(p.potential * (100 - p.current) / 100);
        console.log(`│ ${i + 1}. ${p.layer.padEnd(45)}│`);
        console.log(`│    Current: ${p.current}% → Potential: ${(p.current + p.potential)}% (${impactPoints > 0 ? '+' : ''}${impactPoints} pts)     │`);
        console.log(`│    ${p.adr}${' '.repeat(50 - p.adr.length)}│`);

        for (const task of p.tasks) {
          const wrapped = task.match(/.{1,50}/g) || [];
          for (let j = 0; j < wrapped.length; j++) {
            const prefix = j === 0 ? '│    ◦ ' : '│      ';
            console.log(`${prefix}${wrapped[j]}${' '.repeat(Math.max(0, 50 - wrapped[j].length))}│`);
          }
        }

        if (i < priorities.length - 1) {
          console.log('│                                                          │');
        }
      }

      console.log('└──────────────────────────────────────────────────────────┘');
      console.log(`\nEstimated completion: ${gap > 0 ? 'ADR 2605250700 + 3-month effort' : 'Already at target!'}`);
      console.log('Run "e7m gov coverage-audit" to save current snapshot.\n');
    } catch (err) {
      console.error('Failed to generate coverage plan:', err);
      process.exit(1);
    }
  });
