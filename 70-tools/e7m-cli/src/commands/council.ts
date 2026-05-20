import { Command } from 'commander';
import fs from 'fs/promises';
import path from 'path';
import { findRepoRoot } from '../lib/root.js';

type Seat = { seat: string; name: string; did: string; wallet: string; status: string; confirmed: string };

function parseRosterTable(md: string): Seat[] {
  const lines = md.split('\n');
  const seats: Seat[] = [];
  let inRoster = false;
  for (const line of lines) {
    if (line.startsWith('## Current roster')) inRoster = true;
    else if (inRoster && line.startsWith('## ')) break;
    else if (inRoster && line.startsWith('|') && !line.includes('---') && !line.match(/\|\s*Seat\s*\|/i)) {
      const cells = line.split('|').slice(1, -1).map((c) => c.trim());
      if (cells.length >= 6 && /^\d/.test(cells[0])) {
        seats.push({
          seat: cells[0], name: cells[1], did: cells[2],
          wallet: cells[3], status: cells[4], confirmed: cells[5],
        });
      }
    }
  }
  return seats;
}

function parseDeadline(md: string): Date | null {
  const m = md.match(/through\s+\*\*(\d{4}-\d{2}-\d{2})\*\*/);
  if (!m) return null;
  return new Date(m[1] + 'T23:59:59Z');
}

export const councilCmd = new Command('council').description('Bootstrap Council ops (per ADR-2605192300)');

councilCmd
  .command('status')
  .description('Show Council roster + RFP countdown')
  .action(async () => {
    const root = await findRepoRoot();
    const councilPath = path.join(root, 'COUNCIL.md');
    let md: string;
    try {
      md = await fs.readFile(councilPath, 'utf8');
    } catch {
      console.error(`COUNCIL.md not found at ${councilPath}`);
      process.exit(1);
    }
    const seats = parseRosterTable(md);
    const deadline = parseDeadline(md);

    console.log('Council roster:');
    for (const s of seats) {
      const flag = /confirmed/i.test(s.status) ? 'OK  ' : s.name.includes('(open)') ? 'OPEN' : '... ';
      console.log(`  ${flag}  Seat ${s.seat}  ${s.name.padEnd(20)}  status=${s.status}`);
    }
    console.log('');
    if (deadline) {
      const now = new Date();
      const ms = deadline.getTime() - now.getTime();
      const days = Math.ceil(ms / (24 * 3600 * 1000));
      const label = days > 0 ? `${days} day(s) remaining` : `closed ${-days} day(s) ago`;
      console.log(`RFP deadline: ${deadline.toISOString().slice(0, 10)} (${label})`);
    } else {
      console.log('RFP deadline: (not parseable from COUNCIL.md)');
    }
    const open = seats.filter((s) => s.name.includes('(open)')).length;
    console.log(`Open seats: ${open} / ${seats.length}`);
  });
