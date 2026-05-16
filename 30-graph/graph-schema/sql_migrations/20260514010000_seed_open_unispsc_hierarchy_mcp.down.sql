DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'ai.gftd.apps.openUnispsc.segment',
  'ai.gftd.apps.openUnispsc.family',
  'ai.gftd.apps.openUnispsc.class',
  'ai.gftd.apps.openUnispsc.commodity',
  'ai.gftd.apps.openUnispsc.designItem',
  'ai.gftd.apps.openUnispsc.itemGetSpec',
  'ai.gftd.apps.openUnispsc.itemScreenSupplier',
  'ai.gftd.apps.openUnispsc.itemPlanProcurement',
  'ai.gftd.apps.openUnispsc.itemFlagCompliance',
  'ai.gftd.apps.openUnispsc.syncCatalogItem',
  'ai.gftd.apps.openUnispsc.planCatalogPurchase',
  'ai.gftd.apps.openUnispsc.syncAllCommodityDids',
  'ai.gftd.apps.openUnispsc.importSegmentCatalog',
  'ai.gftd.apps.openUnispsc.supplier',
  'ai.gftd.apps.openUnispsc.procurement',
  'ai.gftd.apps.openUnispsc.flagArmsCommodity',
  'ai.gftd.apps.openUnispsc.flagDualUseCommodity',
  'ai.gftd.apps.openUnispsc.applyGraphWritePlan',
  'ai.gftd.apps.openUnispsc.runItemWorkflow',
  'ai.gftd.apps.openUnispsc.coverageSnapshot'
);

FLUSH;
