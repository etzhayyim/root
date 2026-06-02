#!/usr/bin/env node
/**
 * Generate SEO articles for top vehicles.
 * Priority: spec + review articles for high-demand models.
 */

const CMD = 'https://kuruma.etzhayyim.com/xrpc/etzhayyim.kuruma.v1.KurumaCommandService/GenerateArticle';
const QRY = 'https://kuruma.etzhayyim.com/xrpc/etzhayyim.kuruma.v1.KurumaQueryService/ListVehicles';

async function listVehicles() {
  const res = await fetch(QRY, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ limit: 100, offset: 0 })
  });
  const data = await res.json();
  return data.items || [];
}

async function generateArticle(vehicleId, locale, articleType) {
  const res = await fetch(CMD, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 'vehicle_id': vehicleId, locale, 'article_type': articleType })
  });
  return res.json();
}

async function main() {
  const vehicles = await listVehicles();
  console.log(`Found ${vehicles.length} vehicles. Generating articles...`);

  // Generate spec + review articles for all vehicles (ja first)
  const tasks = [];
  for (const v of vehicles) {
    tasks.push({ vehicle: v, locale: 'ja', type: 'spec' });
    tasks.push({ vehicle: v, locale: 'ja', type: 'review' });
  }

  let ok = 0, fail = 0;
  // Process 3 at a time (LLM calls are slow)
  for (let i = 0; i < tasks.length; i += 3) {
    const batch = tasks.slice(i, i + 3);
    const results = await Promise.all(batch.map(async (t) => {
      try {
        const r = await generateArticle(t.vehicle.vehicle_id, t.locale, t.type);
        return { name: `${t.vehicle.make} ${t.vehicle.model} [${t.type}]`, ok: !!r.article_id, id: r.article_id || r.error };
      } catch (e) {
        return { name: `${t.vehicle.make} ${t.vehicle.model} [${t.type}]`, ok: false, id: String(e) };
      }
    }));

    for (const r of results) {
      if (r.ok) ok++; else fail++;
      console.log(`  [${i + results.indexOf(r) + 1}/${tasks.length}] ${r.name}: ${r.ok ? r.id : 'FAIL ' + r.id}`);
    }
  }

  console.log(`\nDone: ${ok} articles generated, ${fail} failed.`);
}

main().catch(console.error);
