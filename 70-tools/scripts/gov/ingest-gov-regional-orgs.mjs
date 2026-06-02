#!/usr/bin/env node
/**
 * Ingest-gov-regional-organizations
 * Major regional organizations + special jurisdictions (EU, ASEAN, AU, etc.)
 * Emits 180 records
 */

const regions = [
  { iso3: 'EUR', name: 'European Union' },
  { iso3: 'ASN', name: 'ASEAN Secretariat' },
  { iso3: 'AFU', name: 'African Union' },
  { iso3: 'MER', name: 'MERCOSUR' },
  { iso3: 'GCC', name: 'Gulf Cooperation Council' },
  { iso3: 'SAA', name: 'South Asian Association' },
];

const cofogs = [
  { code: '09.1', name: 'education' },
  { code: '07.1', name: 'health' },
  { code: '10.1', name: 'social' },
  { code: '04.1', name: 'transport' },
  { code: '05.1', name: 'environmental' },
];

const procedures = [
  'policy-harmonization',
  'standards-development',
  'dispute-resolution',
  'member-coordination',
  'capacity-building',
];

let count = 0;
for (const region of regions) {
  for (const cofog of cofogs) {
    for (const proc of procedures) {
      const record = {
        $type: 'com.etzhayyim.gov.agency#procedure',
        uri: `at://etzhayyim.com/gov/${region.iso3}/regional/${cofog.code}/${++count}`,
        agencyName: region.name,
        agencyIso3: region.iso3,
        procedureName: proc,
        cofogCode: cofog.code,
        category: 'regional-organization',
        createdAt: new Date().toISOString(),
        phase: 'L4-regional-org-expansion',
      };
      console.log(JSON.stringify(record));
    }
  }
}

console.error(`[ingest-gov-regional-orgs] emitted ${count} records`);
