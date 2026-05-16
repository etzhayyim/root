DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'ai.gftd.apps.openIsicB.classifyMining',
  'ai.gftd.apps.openIsicC.classifyManufacturing',
  'ai.gftd.apps.openIsicD.classifyElectricity',
  'ai.gftd.apps.openIsicE.classifyWater',
  'ai.gftd.apps.openIsicF.classifyConstruction',
  'ai.gftd.apps.openIsicG.classifyTrade',
  'ai.gftd.apps.openIsicH.classifyTransportation',
  'ai.gftd.apps.openIsicI.classifyAccommodation',
  'ai.gftd.apps.openIsicJ.classifyInformation',
  'ai.gftd.apps.openIsicK.classifyFinancial',
  'ai.gftd.apps.openIsicL.classifyRealEstate',
  'ai.gftd.apps.openIsicM.classifyProfessional',
  'ai.gftd.apps.openIsicN.classifyAdministrative',
  'ai.gftd.apps.openIsicO.classifyPublicAdministration',
  'ai.gftd.apps.openIsicP.classifyEducation',
  'ai.gftd.apps.openIsicQ.classifyHealth',
  'ai.gftd.apps.openIsicR.classifyArts',
  'ai.gftd.apps.openIsicS.classifyOtherServices',
  'ai.gftd.apps.openIsicT.classifyHouseholds',
  'ai.gftd.apps.openIsicU.classifyExtraterritorial'
);

FLUSH;
