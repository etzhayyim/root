import { writeFileSync } from 'node:fs';

const locales = {
  ja: {
    spec: '{make} {model} スペック',
    review: '{make} {model} レビュー',
    compare: '{make} {model} 比較',
    ownership: '{make} {model} 維持費',
  },
  en: {
    spec: '{make} {model} specs',
    review: '{make} {model} review',
    compare: '{make} {model} vs competitors',
    ownership: '{make} {model} ownership cost',
  },
  es: {
    spec: 'especificaciones {make} {model}',
    review: 'reseña {make} {model}',
    compare: '{make} {model} vs competidores',
    ownership: 'costo de mantenimiento {make} {model}',
  },
  pt: {
    spec: 'especificacoes {make} {model}',
    review: 'avaliacao {make} {model}',
    compare: '{make} {model} vs concorrentes',
    ownership: 'custo de manutencao {make} {model}',
  },
  de: {
    spec: '{make} {model} technische daten',
    review: '{make} {model} testbericht',
    compare: '{make} {model} vergleich',
    ownership: '{make} {model} unterhaltskosten',
  },
  fr: {
    spec: 'fiche technique {make} {model}',
    review: 'essai {make} {model}',
    compare: '{make} {model} comparaison',
    ownership: 'cout entretien {make} {model}',
  },
};

const models = [
  { make: 'Toyota', model: 'Corolla', cluster: 'c-segment-sedan' },
  { make: 'Toyota', model: 'Prius', cluster: 'hybrid' },
  { make: 'Toyota', model: 'Alphard', cluster: 'minivan' },
  { make: 'Toyota', model: 'Land Cruiser', cluster: 'suv-offroad' },
  { make: 'Honda', model: 'Civic', cluster: 'c-segment-sedan' },
  { make: 'Honda', model: 'N-Box', cluster: 'kei' },
  { make: 'Honda', model: 'Stepwgn', cluster: 'minivan' },
  { make: 'Nissan', model: 'Serena', cluster: 'minivan' },
  { make: 'Nissan', model: 'X-Trail', cluster: 'suv' },
  { make: 'Mazda', model: 'CX-5', cluster: 'suv' },
  { make: 'Subaru', model: 'Forester', cluster: 'suv-awd' },
  { make: 'Suzuki', model: 'Jimny', cluster: 'kei-offroad' },
  { make: 'Mitsubishi', model: 'Delica D:5', cluster: 'minivan-awd' },
  { make: 'Lexus', model: 'RX', cluster: 'luxury-suv' },
  { make: 'Lexus', model: 'NX', cluster: 'luxury-suv' },
  { make: 'Toyota', model: 'HiAce', cluster: 'van' },
];

const intents = ['spec', 'review', 'compare', 'ownership'];

const header = [
  'id',
  'locale',
  'cluster',
  'intent',
  'query',
  'page_type',
  'source_market',
  'priority',
  'notes',
];

const rows = [header.join(',')];
let id = 1;
for (const [locale, dict] of Object.entries(locales)) {
  for (const car of models) {
    for (const intent of intents) {
      const tmpl = dict[intent];
      const query = tmpl.replace('{make}', car.make).replace('{model}', car.model);
      const pageType = intent === 'compare' ? 'compare' : intent === 'ownership' ? 'ownership' : intent;
      const priority =
        locale === 'ja' || locale === 'en'
          ? 'p1'
          : locale === 'es' || locale === 'pt'
          ? 'p2'
          : 'p3';
      const notes =
        locale === 'ja'
          ? 'canonical-source'
          : 'localized-from-ja-with-market-notes';

      rows.push(
        [
          `kw-${String(id).padStart(4, '0')}`,
          locale,
          car.cluster,
          intent,
          `"${query.replaceAll('"', '""')}"`,
          pageType,
          'japan',
          priority,
          notes,
        ].join(',')
      );
      id += 1;
    }
  }
}

writeFileSync(
  new URL('../data/keyword_map_seed.csv', import.meta.url),
  rows.join('\n') + '\n',
  'utf8'
);

console.log(`Generated ${id - 1} keyword rows`);
