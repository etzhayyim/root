DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'com.etzhayyim.apps.openUnispsc.segment',
  'com.etzhayyim.apps.openUnispsc.family',
  'com.etzhayyim.apps.openUnispsc.class',
  'com.etzhayyim.apps.openUnispsc.commodity',
  'com.etzhayyim.apps.openUnispsc.designItem',
  'com.etzhayyim.apps.openUnispsc.itemGetSpec',
  'com.etzhayyim.apps.openUnispsc.itemScreenSupplier',
  'com.etzhayyim.apps.openUnispsc.itemPlanProcurement',
  'com.etzhayyim.apps.openUnispsc.itemFlagCompliance',
  'com.etzhayyim.apps.openUnispsc.syncCatalogItem',
  'com.etzhayyim.apps.openUnispsc.planCatalogPurchase',
  'com.etzhayyim.apps.openUnispsc.syncAllCommodityDids',
  'com.etzhayyim.apps.openUnispsc.importSegmentCatalog',
  'com.etzhayyim.apps.openUnispsc.supplier',
  'com.etzhayyim.apps.openUnispsc.procurement',
  'com.etzhayyim.apps.openUnispsc.flagArmsCommodity',
  'com.etzhayyim.apps.openUnispsc.flagDualUseCommodity',
  'com.etzhayyim.apps.openUnispsc.applyGraphWritePlan',
  'com.etzhayyim.apps.openUnispsc.runItemWorkflow',
  'com.etzhayyim.apps.openUnispsc.coverageSnapshot'
);

FLUSH;
