// Parity harness: squint-compiled tithe.cljs  vs  the original tithe.ts.
// Reproduce:
//   npm i squint-cljs && npx squint-cljs compile tithe.cljs   # → tithe.mjs
//   cp tithe.ts.reference tithe.ts && node parity.mjs
import * as sq from './tithe.mjs';     // squint output of tithe.cljs
import * as ts from './tithe.ts';      // node v26 strips types
const cases = ["0","7","999","1000","1000000","123456789012345"];
let ok=0, fail=0;
for (const c of cases) {
  const a = sq.split_tithe(sq.parse_micros(c));
  const b = ts.splitTithe(ts.parseMicros(c));
  (a.gross===b.gross && a.tithe===b.tithe && a.net===b.net) ? ok++ : fail++;
}
const err = fn => { try { fn(); return 'no-throw'; } catch(e){ return e.constructor.name; } };
console.log(`value parity: ${ok}/${ok+fail}`);
console.log(`no-rounding-leak 7→0: ${sq.split_tithe(7n).tithe===0n}`);
console.log(`neg→ squint:${err(()=>sq.split_tithe(-1n))} ts:${err(()=>ts.splitTithe(-1n))}`);
console.log(`bad→ squint:${err(()=>sq.parse_micros("x"))} ts:${err(()=>ts.parseMicros("x"))}`);
process.exit(fail>0?1:0);
