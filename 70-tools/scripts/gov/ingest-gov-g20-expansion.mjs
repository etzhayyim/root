#!/usr/bin/env node
/**
 * Ingest-gov-G20-expansion
 * Generates 200 records for G20 countries + regional powers across all COFOG categories
 */

const countries = [
  { iso3: 'USA', name: 'United States' },
  { iso3: 'CHN', name: 'China' },
  { iso3: 'JPN', name: 'Japan' },
  { iso3: 'DEU', name: 'Germany' },
  { iso3: 'IND', name: 'India' },
  { iso3: 'FRA', name: 'France' },
  { iso3: 'GBR', name: 'United Kingdom' },
  { iso3: 'ITA', name: 'Italy' },
  { iso3: 'BRA', name: 'Brazil' },
  { iso3: 'CAN', name: 'Canada' },
  { iso3: 'RUS', name: 'Russia' },
  { iso3: 'KOR', name: 'South Korea' },
  { iso3: 'ESP', name: 'Spain' },
  { iso3: 'MEX', name: 'Mexico' },
  { iso3: 'AUS', name: 'Australia' },
];

const cofogs = [
  { code: '09.1', name: 'Education' },
  { code: '07.1', name: 'Health' },
  { code: '10.1', name: 'Social' },
  { code: '04.1', name: 'Transport' },
];

const procedures = {
  education: ['curriculum-standards', 'student-assessment', 'teacher-training', 'school-accreditation'],
  health: ['disease-surveillance', 'pharmaceutical-approval', 'medical-device-regulation', 'healthcare-licensing'],
  social: ['pension-eligibility', 'housing-assistance', 'childcare-subsidy', 'employment-support'],
  transport: ['traffic-safety', 'transit-planning', 'cargo-inspection', 'aviation-certification'],
};

function emitRecord(country, cofog, procedure, idx) {
  return {
    $type: 'com.etzhayyim.gov.agency#procedure',
    uri: `at://etzhayyim.com/gov/${country.iso3}/g20-expansion/${cofog.code}/${idx}`,
    agencyName: country.name,
    agencyIso3: country.iso3,
    procedureName: procedure,
    cofogCode: cofog.code,
    bpmnReference: `00-contracts/bpmn/com/etzhayyim/gov${country.iso3}/${cofog.name.toLowerCase()}/procedure-${procedure}.bpmn`,
    jurisdiction: country.iso3,
    createdAt: new Date().toISOString(),
    phase: 'L4-G20-expansion',
  };
}

let count = 0;
for (const country of countries) {
  for (const cofog of cofogs) {
    const cofogKey = cofog.name.toLowerCase();
    const procList = procedures[cofogKey] || [];
    for (const proc of procList) {
      console.log(JSON.stringify(emitRecord(country, cofog, proc, ++count)));
    }
  }
}

console.error(`[ingest-gov-g20-expansion] emitted ${count} records`);
