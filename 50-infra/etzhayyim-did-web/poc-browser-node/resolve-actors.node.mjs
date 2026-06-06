// PROOF (Node-driven, same wasm artifact as the browser): the browser kotoba node
// resolves the REAL etzhayyim actor set client-side via the SAME path the apex
// Worker tier-2 uses — node.loadDatoms(...) + node.searchActors(q) — plus the
// no-server-key signed content-addressed write path (commitSigned).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { webcrypto } from 'node:crypto';
if (!globalThis.crypto) globalThis.crypto = webcrypto; // getrandom js shim (browser uses crypto.getRandomValues)

const here = dirname(fileURLToPath(import.meta.url));
const { KotobaNode } = await import(resolve(here, 'node-pkg/kotoba_wasm.js'));
const seed = JSON.parse(readFileSync(resolve(here, 'serve/seed-datoms.json'), 'utf8'));

let fails = 0;
const ok = (c, m) => { console.log(`${c ? 'PASS' : 'FAIL'}  ${m}`); if (!c) fails++; };

const node = new KotobaNode();
node.useIdentity('2c'.repeat(32));               // deterministic sovereign identity
const applied = node.loadDatoms(JSON.stringify(seed));
console.log(`loaded ${applied} datoms (${node.datomCount()} total)\n`);

// READ — resolve kamado client-side (the actor that started this thread)
const kamado = JSON.parse(node.searchActors('kamado')).actors;
ok(kamado.length === 1, `searchActors("kamado") → 1 actor`);
ok(kamado[0]?.did === 'did:web:etzhayyim.com:actor:kamado', `kamado did = ${kamado[0]?.did}`);
ok(/竈|Kamado/.test(kamado[0]?.displayName || ''), `kamado displayName = ${kamado[0]?.displayName}`);

// READ — corpus is the real 28-actor set, not a toy fixture
const all = JSON.parse(node.searchActors('')).actors;
ok(all.length >= 27, `searchActors("") → ${all.length} actors (real SSoT)`);
ok(all.some(a => a.handle === 'tsumugi') && all.some(a => a.handle === 'watari'),
   `corpus includes tsumugi + watari`);

// WRITE — no-server-key, content-addressed, member-signed
const signed = JSON.parse(node.commitSigned());
ok(/^did:key:z/.test(signed.did), `commitSigned signer = ${signed.did} (client-side ed25519, no server key)`);
ok(/^bafyrei/.test(signed.root), `content-addressed root = ${signed.root}`);
ok(typeof signed.sig === 'string' && signed.sig.length === 128, `ed25519 signature present (${signed.sig.length} hex)`);

// DETERMINISM — content-addressing: identical input → identical root from a fresh node
const n2 = new KotobaNode(); n2.useIdentity('2c'.repeat(32)); n2.loadDatoms(JSON.stringify(seed)); n2.commitSigned();
ok(node.rootCid() === n2.rootCid(), `deterministic content-addressed root (${n2.rootCid()})`);

console.log(`\n${fails === 0 ? 'ALL PASS' : fails + ' FAILED'} — browser kotoba node resolves the real etzhayyim actor set, no server pull.`);
process.exit(fails === 0 ? 0 : 1);
