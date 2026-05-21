type CoverageActor = {
  did: string;
  displayName: string;
  stage: string;
  jurisdiction: string;
  priority: number;
  deps: string[];
};

type CoverageFlow = {
  source: string;
  target: string;
  kind: string;
  status: string;
};

type MineralRegistry = {
  did: string;
  displayName: string;
  priority: number;
  deps: string[];
  keySectors: string[];
  coverage: 'baseline' | 'expanded';
};

const actors: CoverageActor[] = [
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:rare-earth', displayName: 'Rare Earth Mineral System', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:global-ev-oem', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-wind-oem', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:ndpr', displayName: 'NdPr Mineral Subsystem', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:operator:mp-materials', 'did:web:rare-earth-coverage.etzhayyim.com:processor:china-northern-rare-earth'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:dytb', displayName: 'Dy/Tb Mineral Subsystem', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:processor:china-rare-earth-group', 'did:web:rare-earth-coverage.etzhayyim.com:resource:myanmar-ion-clays'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:tungsten', displayName: 'Tungsten Mineral System', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:china-tungsten-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:us-tungsten-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:antimony', displayName: 'Antimony Mineral System', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:china-antimony-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:us-antimony-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:eu-antimony-sector'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:gallium', displayName: 'Gallium Mineral System', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:germanium', displayName: 'Germanium Mineral System', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:graphite', displayName: 'Graphite Mineral System', stage: 'taxonomy', jurisdiction: 'GLOBAL', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:global-ev-oem', 'did:web:rare-earth-coverage.etzhayyim.com:sector:china-magnet-sector'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:regulator:china-state-council', displayName: 'State Council of China', stage: 'policy', jurisdiction: 'CN', priority: 1, deps: [] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom', displayName: 'MOFCOM', stage: 'policy', jurisdiction: 'CN', priority: 1, deps: [] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:processor:china-northern-rare-earth', displayName: 'China Northern Rare Earth Group', stage: 'separation', jurisdiction: 'CN', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:resource:bayan-obo'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:processor:china-rare-earth-group', displayName: 'China Rare Earth Group', stage: 'separation', jurisdiction: 'CN', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:resource:southern-ion-clays', 'did:web:rare-earth-coverage.etzhayyim.com:resource:myanmar-ion-clays'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:processor:shenghe-resources', displayName: 'Shenghe Resources', stage: 'processing', jurisdiction: 'CN', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:china-magnet-sector'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:jl-mag', displayName: 'JL MAG Rare-Earth', stage: 'magnet-manufacturing', jurisdiction: 'CN', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:processor:shenghe-resources'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:zhong-ke-san-huan', displayName: 'Zhong Ke San Huan', stage: 'magnet-manufacturing', jurisdiction: 'CN', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:processor:china-northern-rare-earth'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:beijing-zhong-ke-san-huan', displayName: 'Beijing Zhong Ke San Huan Magnetics', stage: 'magnet-manufacturing', jurisdiction: 'CN', priority: 3, deps: ['did:web:rare-earth-coverage.etzhayyim.com:magnet:zhong-ke-san-huan'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:china-magnet-sector', displayName: 'China Permanent Magnet Sector', stage: 'magnet-manufacturing', jurisdiction: 'CN', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:processor:china-northern-rare-earth', 'did:web:rare-earth-coverage.etzhayyim.com:processor:china-rare-earth-group'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:china-tungsten-sector', displayName: 'China Tungsten Sector', stage: 'processing', jurisdiction: 'CN', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:tungsten', 'did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:china-antimony-sector', displayName: 'China Antimony Sector', stage: 'processing', jurisdiction: 'CN', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:antimony', 'did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:operator:mp-materials', displayName: 'MP Materials', stage: 'separation', jurisdiction: 'US', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:resource:mountain-pass', 'did:web:rare-earth-coverage.etzhayyim.com:financer:us-dod-osc'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:plant:mp-independence-texas', displayName: 'MP Independence Magnetics Facility', stage: 'magnet-manufacturing', jurisdiction: 'US', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:operator:mp-materials'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:recycling:urban-mining-company', displayName: 'Urban Mining Company', stage: 'magnet-manufacturing', jurisdiction: 'US', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:processor:reelement-technologies'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:processor:reelement-technologies', displayName: 'ReElement Technologies', stage: 'separation', jurisdiction: 'US', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:recycling:urban-mining-company'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:arnold-magnetic', displayName: 'Arnold Magnetic Technologies', stage: 'magnet-manufacturing', jurisdiction: 'US', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:us-tungsten-sector', displayName: 'U.S. Tungsten Sector', stage: 'processing', jurisdiction: 'US', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:tungsten'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:us-antimony-sector', displayName: 'U.S. Antimony Sector', stage: 'processing', jurisdiction: 'US', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:antimony'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:operator:lynas-rare-earths', displayName: 'Lynas Rare Earths', stage: 'separation', jurisdiction: 'AU', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:resource:mt-weld', 'did:web:rare-earth-coverage.etzhayyim.com:plant:lynas-malaysia'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:plant:lynas-malaysia', displayName: 'Lynas Malaysia', stage: 'separation', jurisdiction: 'MY', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:operator:lynas-rare-earths'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:trader:sojitz', displayName: 'Sojitz', stage: 'finance', jurisdiction: 'JP', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:operator:lynas-rare-earths'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:processor:neo-performance-materials', displayName: 'Neo Performance Materials', stage: 'magnet-manufacturing', jurisdiction: 'CA', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:plant:lynas-malaysia'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:recycling:hypromag', displayName: 'HyProMag', stage: 'magnet-manufacturing', jurisdiction: 'GB', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:metal:less-common-metals'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:metal:less-common-metals', displayName: 'Less Common Metals', stage: 'processing', jurisdiction: 'GB', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:magnet:vacuumschmelze'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:vacuumschmelze', displayName: 'VACUUMSCHMELZE', stage: 'magnet-manufacturing', jurisdiction: 'DE', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:metal:less-common-metals', 'did:web:rare-earth-coverage.etzhayyim.com:processor:solvay'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:proterial', displayName: 'Proterial', stage: 'magnet-manufacturing', jurisdiction: 'JP', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:plant:lynas-malaysia'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:magnet:tdk', displayName: 'TDK', stage: 'magnet-manufacturing', jurisdiction: 'JP', priority: 3, deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:global-ev-oem'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:processor:solvay', displayName: 'Solvay', stage: 'separation', jurisdiction: 'FR', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:magnet:vacuumschmelze'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:operator:iluka-resources', displayName: 'Iluka Resources', stage: 'separation', jurisdiction: 'AU', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:plant:eneabba-refinery'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:operator:caremag', displayName: 'Caremag SAS', stage: 'separation', jurisdiction: 'FR', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:financer:jogmec'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:eu-antimony-sector', displayName: 'EU Antimony Sector', stage: 'processing', jurisdiction: 'EU', priority: 2, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:antimony'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:financer:jogmec', displayName: 'JOGMEC', stage: 'finance', jurisdiction: 'JP', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:operator:caremag'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-ev-oem', displayName: 'Global EV OEM Cluster', stage: 'demand', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:rare-earth', 'did:web:rare-earth-coverage.etzhayyim.com:mineral:graphite'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-wind-oem', displayName: 'Global Wind Turbine OEM Cluster', stage: 'demand', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:rare-earth', 'did:web:rare-earth-coverage.etzhayyim.com:mineral:tungsten'] },
  { did: 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem', displayName: 'Global Defense OEM Cluster', stage: 'demand', jurisdiction: 'GLOBAL', priority: 1, deps: ['did:web:rare-earth-coverage.etzhayyim.com:mineral:rare-earth', 'did:web:rare-earth-coverage.etzhayyim.com:mineral:tungsten', 'did:web:rare-earth-coverage.etzhayyim.com:mineral:antimony', 'did:web:rare-earth-coverage.etzhayyim.com:mineral:gallium', 'did:web:rare-earth-coverage.etzhayyim.com:mineral:germanium'] }
];

const flows: CoverageFlow[] = [
  { source: 'Rare Earth Mineral System', target: 'Global EV OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Rare Earth Mineral System', target: 'Global Wind Turbine OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Rare Earth Mineral System', target: 'Global Defense OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Tungsten Mineral System', target: 'Global Defense OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Antimony Mineral System', target: 'Global Defense OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Gallium Mineral System', target: 'Global Defense OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Germanium Mineral System', target: 'Global Defense OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'Graphite Mineral System', target: 'Global EV OEM Cluster', kind: 'dependency', status: 'active' },
  { source: 'State Council of China', target: 'MOFCOM', kind: 'policy', status: 'active' },
  { source: 'MOFCOM', target: 'China Tungsten Sector', kind: 'regulation', status: 'active' },
  { source: 'MOFCOM', target: 'China Antimony Sector', kind: 'regulation', status: 'active' },
  { source: 'China Tungsten Sector', target: 'Tungsten Mineral System', kind: 'dependency', status: 'active' },
  { source: 'China Antimony Sector', target: 'Antimony Mineral System', kind: 'dependency', status: 'active' },
  { source: 'U.S. Tungsten Sector', target: 'Tungsten Mineral System', kind: 'dependency', status: 'active' },
  { source: 'U.S. Antimony Sector', target: 'Antimony Mineral System', kind: 'dependency', status: 'active' },
  { source: 'EU Antimony Sector', target: 'Antimony Mineral System', kind: 'dependency', status: 'active' },
  { source: 'Bayan Obo Resource Base', target: 'China Northern Rare Earth Group', kind: 'resource_flow', status: 'active' },
  { source: 'Myanmar Ion-Adsorption Clay Sector', target: 'China Rare Earth Group', kind: 'resource_flow', status: 'active' },
  { source: 'China Northern Rare Earth Group', target: 'China Permanent Magnet Sector', kind: 'resource_flow', status: 'active' },
  { source: 'Shenghe Resources', target: 'JL MAG Rare-Earth', kind: 'resource_flow', status: 'active' },
  { source: 'China Northern Rare Earth Group', target: 'Zhong Ke San Huan', kind: 'resource_flow', status: 'active' },
  { source: 'Zhong Ke San Huan', target: 'Beijing Zhong Ke San Huan Magnetics', kind: 'resource_flow', status: 'active' },
  { source: 'JL MAG Rare-Earth', target: 'Global EV OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'Zhong Ke San Huan', target: 'Global Wind Turbine OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'China Permanent Magnet Sector', target: 'Global EV OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'China Permanent Magnet Sector', target: 'Global Defense OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'U.S. DoD / Office of Strategic Capital', target: 'MP Materials', kind: 'capital_flow', status: 'active' },
  { source: 'MP Materials', target: 'MP Independence Magnetics Facility', kind: 'resource_flow', status: 'active' },
  { source: 'ReElement Technologies', target: 'Urban Mining Company', kind: 'resource_flow', status: 'active' },
  { source: 'Urban Mining Company', target: 'Global Defense OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'Arnold Magnetic Technologies', target: 'Global Defense OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'Mt Weld', target: 'Lynas Malaysia', kind: 'resource_flow', status: 'active' },
  { source: 'Sojitz', target: 'Lynas Rare Earths', kind: 'capital_flow', status: 'active' },
  { source: 'Lynas Malaysia', target: 'Proterial', kind: 'resource_flow', status: 'active' },
  { source: 'Lynas Malaysia', target: 'Neo Performance Materials', kind: 'resource_flow', status: 'active' },
  { source: 'Lynas Malaysia', target: 'Global EV OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'Less Common Metals', target: 'VACUUMSCHMELZE', kind: 'resource_flow', status: 'active' },
  { source: 'HyProMag', target: 'Global Wind Turbine OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'Solvay', target: 'VACUUMSCHMELZE', kind: 'resource_flow', status: 'active' },
  { source: 'TDK', target: 'Global EV OEM Cluster', kind: 'resource_flow', status: 'active' },
  { source: 'JOGMEC', target: 'Caremag SAS', kind: 'capital_flow', status: 'active' },
  { source: 'Iluka Resources', target: 'Eneabba Rare Earths Refinery', kind: 'project', status: 'planned' },
  { source: 'Caremag SAS', target: 'Global Defense OEM Cluster', kind: 'resource_flow', status: 'planned' }
];

const minerals: MineralRegistry[] = [
  {
    did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:rare-earth',
    displayName: 'Rare Earth Mineral System',
    priority: 1,
    deps: ['did:web:rare-earth-coverage.etzhayyim.com:processor:china-northern-rare-earth', 'did:web:rare-earth-coverage.etzhayyim.com:operator:mp-materials', 'did:web:rare-earth-coverage.etzhayyim.com:operator:lynas-rare-earths'],
    keySectors: ['EV', 'Wind', 'Defense'],
    coverage: 'baseline'
  },
  {
    did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:tungsten',
    displayName: 'Tungsten Mineral System',
    priority: 1,
    deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:china-tungsten-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:us-tungsten-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'],
    keySectors: ['Defense', 'Tooling', 'Wind'],
    coverage: 'expanded'
  },
  {
    did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:antimony',
    displayName: 'Antimony Mineral System',
    priority: 1,
    deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:china-antimony-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:us-antimony-sector', 'did:web:rare-earth-coverage.etzhayyim.com:sector:eu-antimony-sector'],
    keySectors: ['Defense', 'Flame Retardants', 'Chemicals'],
    coverage: 'expanded'
  },
  {
    did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:gallium',
    displayName: 'Gallium Mineral System',
    priority: 2,
    deps: ['did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'],
    keySectors: ['Defense', 'Semiconductors', 'RF'],
    coverage: 'expanded'
  },
  {
    did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:germanium',
    displayName: 'Germanium Mineral System',
    priority: 2,
    deps: ['did:web:rare-earth-coverage.etzhayyim.com:regulator:china-mofcom', 'did:web:rare-earth-coverage.etzhayyim.com:sector:global-defense-oem'],
    keySectors: ['Defense', 'Optics', 'Infrared'],
    coverage: 'expanded'
  },
  {
    did: 'did:web:rare-earth-coverage.etzhayyim.com:mineral:graphite',
    displayName: 'Graphite Mineral System',
    priority: 2,
    deps: ['did:web:rare-earth-coverage.etzhayyim.com:sector:global-ev-oem', 'did:web:rare-earth-coverage.etzhayyim.com:sector:china-magnet-sector'],
    keySectors: ['EV', 'Batteries', 'Processing'],
    coverage: 'expanded'
  }
];

const stageCoverage = Object.entries(
  actors.reduce<Record<string, number>>((acc, actor) => {
    acc[actor.stage] = (acc[actor.stage] ?? 0) + 1;
    return acc;
  }, {})
)
  .map(([stage, count]) => ({ stage, count }))
  .sort((a, b) => b.count - a.count || a.stage.localeCompare(b.stage));

const jurisdictions = new Set(actors.map((actor) => actor.jurisdiction));

export const coverageData = {
  updatedAt: '2026-04-13T19:10:00Z',
  primaryActorDid: 'did:web:rare-earth-coverage.etzhayyim.com',
  appviewDid: 'did:web:rare-earth.etzhayyim.com',
  metrics: {
    actorCount: actors.length,
    flowCount: flows.length,
    jurisdictionCount: jurisdictions.size,
    activeDiversificationProjects: flows.filter((flow) => flow.status === 'planned' || flow.kind === 'capital_flow').length,
    mineralCount: minerals.length
  },
  bottlenecks: [
    {
      title: 'China concentration now spans multiple minerals',
      detail: 'Rare earths, tungsten, antimony, gallium, and germanium all show China-linked regulatory or processing concentration in the registered dependency graph.',
      severity: 'critical'
    },
    {
      title: 'Heavy rare earth exposure',
      detail: 'Dy/Tb exposure remains tied to southern China and Myanmar-linked upstream clusters even as non-China refining nodes expand.',
      severity: 'high'
    },
    {
      title: 'Thin non-China processing depth',
      detail: 'The graph now covers more mineral systems, but non-China refining and metal conversion pathways remain much thinner than demand-side dependency.',
      severity: 'high'
    }
  ],
  stageCoverage,
  minerals,
  actors,
  flows
} as const;

export type CoverageData = typeof coverageData;
