// Convert the REAL committed actor-profile SSoT
// (00-contracts/schemas/actor-profile-seed.kotoba.edn) into the `:yoro.profile/*`
// datom shape the browser kotoba node (kotoba-wasm) hydrates + searches.
//
// This is the same data the apex Worker's tier-2 (kg.entity) serves — proving the
// browser node resolves the ACTUAL etzhayyim actor set client-side, not a toy fixture.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const seedPath = resolve(here, '../../../00-contracts/schemas/actor-profile-seed.kotoba.edn');
const edn = readFileSync(seedPath, 'utf8');

// Split into actor records by the stable `{:actor/handle` boundary, then pull the
// four profile fields with targeted regexes (one of each per record).
const field = (block, key) => {
  const m = block.match(new RegExp(`:actor/${key}\\s+"((?:[^"\\\\]|\\\\.)*)"`));
  return m ? m[1].replace(/\\"/g, '"') : null;
};
const chunks = edn.split(/\{\s*:actor\/handle/).slice(1);
const datoms = [];
let n = 0;
for (const raw of chunks) {
  const block = '{:actor/handle' + raw;
  const handle = field(block, 'handle');
  if (!handle) continue;
  const did = field(block, 'did') || `did:web:etzhayyim.com:actor:${handle}`;
  const dn = field(block, 'display-name-en') || field(block, 'display-name-ja') || handle;
  const desc = field(block, 'description') || '';
  const e = `actor:${handle}`;
  datoms.push({ e, a: ':yoro.profile/did', v_edn: JSON.stringify(did), added: true });
  datoms.push({ e, a: ':yoro.profile/handle', v_edn: JSON.stringify(handle), added: true });
  datoms.push({ e, a: ':yoro.profile/displayName', v_edn: JSON.stringify(dn), added: true });
  datoms.push({ e, a: ':yoro.profile/description', v_edn: JSON.stringify(desc), added: true });
  n++;
}
const out = resolve(here, 'serve/seed-datoms.json');
writeFileSync(out, JSON.stringify(datoms));
console.log(`generated ${datoms.length} datoms for ${n} actors → ${out}`);
console.log('kamado present:', datoms.some(d => d.a === ':yoro.profile/handle' && d.v_edn === '"kamado"'));
