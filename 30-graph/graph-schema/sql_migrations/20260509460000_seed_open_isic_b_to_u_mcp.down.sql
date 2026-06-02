DELETE FROM vertex_mcp_tool_def
WHERE nsid IN (
  'com.etzhayyim.apps.openIsicB.classifyMining',
  'com.etzhayyim.apps.openIsicC.classifyManufacturing',
  'com.etzhayyim.apps.openIsicD.classifyElectricity',
  'com.etzhayyim.apps.openIsicE.classifyWater',
  'com.etzhayyim.apps.openIsicF.classifyConstruction',
  'com.etzhayyim.apps.openIsicG.classifyTrade',
  'com.etzhayyim.apps.openIsicH.classifyTransportation',
  'com.etzhayyim.apps.openIsicI.classifyAccommodation',
  'com.etzhayyim.apps.openIsicJ.classifyInformation',
  'com.etzhayyim.apps.openIsicK.classifyFinancial',
  'com.etzhayyim.apps.openIsicL.classifyRealEstate',
  'com.etzhayyim.apps.openIsicM.classifyProfessional',
  'com.etzhayyim.apps.openIsicN.classifyAdministrative',
  'com.etzhayyim.apps.openIsicO.classifyPublicAdministration',
  'com.etzhayyim.apps.openIsicP.classifyEducation',
  'com.etzhayyim.apps.openIsicQ.classifyHealth',
  'com.etzhayyim.apps.openIsicR.classifyArts',
  'com.etzhayyim.apps.openIsicS.classifyOtherServices',
  'com.etzhayyim.apps.openIsicT.classifyHouseholds',
  'com.etzhayyim.apps.openIsicU.classifyExtraterritorial'
);

FLUSH;
