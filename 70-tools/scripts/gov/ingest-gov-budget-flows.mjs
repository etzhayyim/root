#!/usr/bin/env node
/**
 * Ingest-gov-budget-flows
 *
 * Government budget records: appropriations, allocations, cash flows
 * Represents funding streams between orgs and across jurisdictional levels.
 *
 * Sample: 10 countries × 5 major budget categories × 5 orgs = 250 records
 * Models: national budget → ministry allocation → agency execution → program delivery
 */

const countries = ['USA', 'CHN', 'IND', 'JPN', 'DEU', 'GBR', 'FRA', 'BRA', 'RUS', 'MEX'];

const budget_categories = [
  { code: 'EDU', name: 'Education', cofog: '09' },
  { code: 'HLT', name: 'Health', cofog: '07' },
  { code: 'SOC', name: 'Social Protection', cofog: '10' },
  { code: 'DEF', name: 'Defense', cofog: '02' },
  { code: 'ENG', name: 'Economic Affairs', cofog: '04' },
];

const budget_levels = [
  { level: 'national-budget', name: 'National Budget Appropriation' },
  { level: 'ministry-allocation', name: 'Ministry Budget Allocation' },
  { level: 'agency-execution', name: 'Agency Execution Plan' },
  { level: 'program-delivery', name: 'Program Service Delivery' },
  { level: 'subnational-transfer', name: 'Subnational Transfer' },
];

let budget_count = 0;

function emitBudgetRecord(country, category, budget_level, fiscal_year) {
  const timestamp = new Date().toISOString();
  // Simulate budget amounts in thousands USD
  const base_amount = Math.floor(Math.random() * 500000) + 10000;

  return {
    $type: 'com.etzhayyim.gov.budget#budgetRecord',
    uri: `at://etzhayyim.com/gov/${country}/budget/${fiscal_year}/${++budget_count}`,
    countryIso3: country,
    budgetCategory: category.code,
    budgetLevel: budget_level.level,
    cofogCode: category.cofog,
    budgetAmountUSD: base_amount * 1000,  // in USD
    currencyCode: 'USD',
    fiscalYear: fiscal_year,
    budgetPhase: 'appropriation',
    createdAt: timestamp,
    phase: 'budget-flows-global',
  };
}

const fiscal_year = 2026;

for (const country of countries) {
  for (const category of budget_categories) {
    for (const budget_level of budget_levels) {
      console.log(JSON.stringify(emitBudgetRecord(country, category, budget_level, fiscal_year)));
    }
  }
}

console.error(
  `[ingest-gov-budget-flows] emitted ${budget_count} records (FY${fiscal_year})\n` +
  `Coverage: 10 countries × 5 budget categories × 5 budget levels\n` +
  `Models: national appropriation → ministry allocation → agency execution → program delivery + subnational transfers\n` +
  `Scalable: ×20 for 196 countries = ${budget_count * 20} total budget flow records`
);
