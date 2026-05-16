import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { op: string; processId: string; nsid: string; sourcePath: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:maps.gftd.ai";
const createdAt = "2026-04-30T22:04:00+09:00";
const actorId = "sys.bpmn.seed.maps-collection";

const seeds: Seed[] = [
  { op: "registerSource", processId: "maps_collection_registerSource", nsid: "ai.gftd.apps.maps.registerSource", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/registerSource.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listSources", processId: "maps_collection_listSources", nsid: "ai.gftd.apps.maps.listSources", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/listSources.bpmn", writeTableAllowlist: "" },
  { op: "createCollectionJob", processId: "maps_collection_createCollectionJob", nsid: "ai.gftd.apps.maps.createCollectionJob", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/createCollectionJob.bpmn", writeTableAllowlist: "vertex_spatial,vertex_maps_job" },
  { op: "advanceJob", processId: "maps_collection_advanceJob", nsid: "ai.gftd.apps.maps.advanceJob", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/advanceJob.bpmn", writeTableAllowlist: "vertex_spatial,vertex_maps_job" },
  { op: "listJobs", processId: "maps_collection_listJobs", nsid: "ai.gftd.apps.maps.listJobs", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/listJobs.bpmn", writeTableAllowlist: "" },
  { op: "getJobStatus", processId: "maps_collection_getJobStatus", nsid: "ai.gftd.apps.maps.getJobStatus", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/getJobStatus.bpmn", writeTableAllowlist: "" },
  { op: "storeDataset", processId: "maps_collection_storeDataset", nsid: "ai.gftd.apps.maps.storeDataset", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/storeDataset.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "getDataset", processId: "maps_collection_getDataset", nsid: "ai.gftd.apps.maps.getDataset", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/getDataset.bpmn", writeTableAllowlist: "" },
  { op: "listDatasets", processId: "maps_collection_listDatasets", nsid: "ai.gftd.apps.maps.listDatasets", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/listDatasets.bpmn", writeTableAllowlist: "" },
  { op: "getPipelineStats", processId: "maps_collection_getPipelineStats", nsid: "ai.gftd.apps.maps.getPipelineStats", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/getPipelineStats.bpmn", writeTableAllowlist: "" },
  { op: "importOsmPois", processId: "maps_collection_importOsmPois", nsid: "ai.gftd.apps.maps.importOsmPois", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/importOsmPois.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "importWikidataPois", processId: "maps_collection_importWikidataPois", nsid: "ai.gftd.apps.maps.importWikidataPois", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/importWikidataPois.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "searchPoi", processId: "maps_collection_searchPoi", nsid: "ai.gftd.apps.maps.searchPoi", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/searchPoi.bpmn", writeTableAllowlist: "" },
  { op: "getPoi", processId: "maps_collection_getPoi", nsid: "ai.gftd.apps.maps.getPoi", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/getPoi.bpmn", writeTableAllowlist: "" },
  { op: "listPoiTypes", processId: "maps_collection_listPoiTypes", nsid: "ai.gftd.apps.maps.listPoiTypes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/listPoiTypes.bpmn", writeTableAllowlist: "" },
  { op: "registerWriterProfiles", processId: "maps_collection_registerWriterProfiles", nsid: "ai.gftd.apps.maps.registerWriterProfiles", sourcePath: "00-contracts/bpmn/ai/gftd/maps/collection/registerWriterProfiles.bpmn", writeTableAllowlist: "" },
  { op: "getCoverageStatus", processId: "maps_coverage_getCoverageStatus", nsid: "ai.gftd.apps.maps.getCoverageStatus", sourcePath: "00-contracts/bpmn/ai/gftd/maps/coverage/getCoverageStatus.bpmn", writeTableAllowlist: "" },
  { op: "expandFrontier", processId: "maps_coverage_expandFrontier", nsid: "ai.gftd.apps.maps.expandFrontier", sourcePath: "00-contracts/bpmn/ai/gftd/maps/coverage/expandFrontier.bpmn", writeTableAllowlist: "vertex_maps_coverage_target" },
  { op: "refreshCoverageStats", processId: "maps_coverage_refreshCoverageStats", nsid: "ai.gftd.apps.maps.refreshCoverageStats", sourcePath: "00-contracts/bpmn/ai/gftd/maps/coverage/refreshCoverageStats.bpmn", writeTableAllowlist: "vertex_maps_coverage_target" },
  { op: "advanceCoverage", processId: "maps_coverage_advanceCoverage", nsid: "ai.gftd.apps.maps.advanceCoverage", sourcePath: "00-contracts/bpmn/ai/gftd/maps/coverage/advanceCoverage.bpmn", writeTableAllowlist: "vertex_spatial,vertex_maps_job,vertex_maps_coverage_target" },
  { op: "seedAllKnownVariations", processId: "maps_coverage_seedAllKnownVariations", nsid: "ai.gftd.apps.maps.seedAllKnownVariations", sourcePath: "00-contracts/bpmn/ai/gftd/maps/coverage/seedAllKnownVariations.bpmn", writeTableAllowlist: "vertex_maps_coverage_target" },
  { op: "batchCoverageCycle", processId: "maps_coverage_batchCoverageCycle", nsid: "ai.gftd.apps.maps.batchCoverageCycle", sourcePath: "00-contracts/bpmn/ai/gftd/maps/coverage/batchCoverageCycle.bpmn", writeTableAllowlist: "vertex_spatial,vertex_maps_job,vertex_maps_coverage_target" },
  { op: "registerRegion", processId: "maps_geo_registerRegion", nsid: "ai.gftd.apps.maps.registerRegion", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/registerRegion.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "resolveGeoAlias", processId: "maps_geo_resolveGeoAlias", nsid: "ai.gftd.apps.maps.resolveGeoAlias", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/resolveGeoAlias.bpmn", writeTableAllowlist: "" },
  { op: "listGeoAliases", processId: "maps_geo_listGeoAliases", nsid: "ai.gftd.apps.maps.listGeoAliases", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/listGeoAliases.bpmn", writeTableAllowlist: "" },
  { op: "listGeoSchemes", processId: "maps_geo_listGeoSchemes", nsid: "ai.gftd.apps.maps.listGeoSchemes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/listGeoSchemes.bpmn", writeTableAllowlist: "" },
  { op: "listVerticalZones", processId: "maps_geo_listVerticalZones", nsid: "ai.gftd.apps.maps.listVerticalZones", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/listVerticalZones.bpmn", writeTableAllowlist: "" },
  { op: "listNaturalZones", processId: "maps_geo_listNaturalZones", nsid: "ai.gftd.apps.maps.listNaturalZones", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/listNaturalZones.bpmn", writeTableAllowlist: "" },
  { op: "listLayerCoordinators", processId: "maps_geo_listLayerCoordinators", nsid: "ai.gftd.apps.maps.listLayerCoordinators", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/listLayerCoordinators.bpmn", writeTableAllowlist: "" },
  { op: "resolveZones3d", processId: "maps_geo_resolveZones3d", nsid: "ai.gftd.apps.maps.resolveZones3d", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geo/resolveZones3d.bpmn", writeTableAllowlist: "" },
  { op: "crawlerLocations", processId: "maps_place_crawlerLocations", nsid: "ai.gftd.apps.maps.crawlerLocations", sourcePath: "00-contracts/bpmn/ai/gftd/maps/place/crawlerLocations.bpmn", writeTableAllowlist: "" },
  { op: "searchPlaces", processId: "maps_place_searchPlaces", nsid: "ai.gftd.apps.maps.searchPlaces", sourcePath: "00-contracts/bpmn/ai/gftd/maps/place/searchPlaces.bpmn", writeTableAllowlist: "" },
  { op: "getPlace", processId: "maps_place_getPlace", nsid: "ai.gftd.apps.maps.getPlace", sourcePath: "00-contracts/bpmn/ai/gftd/maps/place/getPlace.bpmn", writeTableAllowlist: "" },
  { op: "graphTraverse", processId: "maps_graph_graphTraverse", nsid: "ai.gftd.apps.maps.graphTraverse", sourcePath: "00-contracts/bpmn/ai/gftd/maps/graph/graphTraverse.bpmn", writeTableAllowlist: "" },
  { op: "graphNeighbors", processId: "maps_graph_graphNeighbors", nsid: "ai.gftd.apps.maps.graphNeighbors", sourcePath: "00-contracts/bpmn/ai/gftd/maps/graph/graphNeighbors.bpmn", writeTableAllowlist: "" },
  { op: "searchResources", processId: "maps_graph_searchResources", nsid: "ai.gftd.apps.maps.searchResources", sourcePath: "00-contracts/bpmn/ai/gftd/maps/graph/searchResources.bpmn", writeTableAllowlist: "" },
  { op: "registerRoute", processId: "maps_transport_registerRoute", nsid: "ai.gftd.apps.maps.registerRoute", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/registerRoute.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listRoutes", processId: "maps_transport_listRoutes", nsid: "ai.gftd.apps.maps.listRoutes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/listRoutes.bpmn", writeTableAllowlist: "" },
  { op: "getRoute", processId: "maps_transport_getRoute", nsid: "ai.gftd.apps.maps.getRoute", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/getRoute.bpmn", writeTableAllowlist: "" },
  { op: "registerRoad", processId: "maps_transport_registerRoad", nsid: "ai.gftd.apps.maps.registerRoad", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/registerRoad.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listRoads", processId: "maps_transport_listRoads", nsid: "ai.gftd.apps.maps.listRoads", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/listRoads.bpmn", writeTableAllowlist: "" },
  { op: "registerRailway", processId: "maps_transport_registerRailway", nsid: "ai.gftd.apps.maps.registerRailway", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/registerRailway.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listRailways", processId: "maps_transport_listRailways", nsid: "ai.gftd.apps.maps.listRailways", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/listRailways.bpmn", writeTableAllowlist: "" },
  { op: "registerSeaRoute", processId: "maps_transport_registerSeaRoute", nsid: "ai.gftd.apps.maps.registerSeaRoute", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/registerSeaRoute.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listSeaRoutes", processId: "maps_transport_listSeaRoutes", nsid: "ai.gftd.apps.maps.listSeaRoutes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/listSeaRoutes.bpmn", writeTableAllowlist: "" },
  { op: "registerAirRoute", processId: "maps_transport_registerAirRoute", nsid: "ai.gftd.apps.maps.registerAirRoute", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/registerAirRoute.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listAirRoutes", processId: "maps_transport_listAirRoutes", nsid: "ai.gftd.apps.maps.listAirRoutes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/listAirRoutes.bpmn", writeTableAllowlist: "" },
  { op: "registerBusRoute", processId: "maps_transport_registerBusRoute", nsid: "ai.gftd.apps.maps.registerBusRoute", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/registerBusRoute.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listBusRoutes", processId: "maps_transport_listBusRoutes", nsid: "ai.gftd.apps.maps.listBusRoutes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport/listBusRoutes.bpmn", writeTableAllowlist: "" },
  { op: "registerInfraNetwork", processId: "maps_infra_registerInfraNetwork", nsid: "ai.gftd.apps.maps.registerInfraNetwork", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/registerInfraNetwork.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listInfraNetworks", processId: "maps_infra_listInfraNetworks", nsid: "ai.gftd.apps.maps.listInfraNetworks", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/listInfraNetworks.bpmn", writeTableAllowlist: "" },
  { op: "registerInfraSegment", processId: "maps_infra_registerInfraSegment", nsid: "ai.gftd.apps.maps.registerInfraSegment", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/registerInfraSegment.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listInfraSegments", processId: "maps_infra_listInfraSegments", nsid: "ai.gftd.apps.maps.listInfraSegments", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/listInfraSegments.bpmn", writeTableAllowlist: "" },
  { op: "registerInfraNode", processId: "maps_infra_registerInfraNode", nsid: "ai.gftd.apps.maps.registerInfraNode", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/registerInfraNode.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listInfraNodes", processId: "maps_infra_listInfraNodes", nsid: "ai.gftd.apps.maps.listInfraNodes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/listInfraNodes.bpmn", writeTableAllowlist: "" },
  { op: "registerInfraIncident", processId: "maps_infra_registerInfraIncident", nsid: "ai.gftd.apps.maps.registerInfraIncident", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/registerInfraIncident.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listInfraIncidents", processId: "maps_infra_listInfraIncidents", nsid: "ai.gftd.apps.maps.listInfraIncidents", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/listInfraIncidents.bpmn", writeTableAllowlist: "" },
  { op: "infraQuery", processId: "maps_infra_infraQuery", nsid: "ai.gftd.apps.maps.infraQuery", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/infraQuery.bpmn", writeTableAllowlist: "" },
  { op: "infraCrossSection", processId: "maps_infra_infraCrossSection", nsid: "ai.gftd.apps.maps.infraCrossSection", sourcePath: "00-contracts/bpmn/ai/gftd/maps/infra/infraCrossSection.bpmn", writeTableAllowlist: "" },
  { op: "registerSpot", processId: "maps_geography_registerSpot", nsid: "ai.gftd.apps.maps.registerSpot", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerSpot.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listSpots", processId: "maps_geography_listSpots", nsid: "ai.gftd.apps.maps.listSpots", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listSpots.bpmn", writeTableAllowlist: "" },
  { op: "getSpot", processId: "maps_geography_getSpot", nsid: "ai.gftd.apps.maps.getSpot", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/getSpot.bpmn", writeTableAllowlist: "" },
  { op: "spotSearch", processId: "maps_geography_spotSearch", nsid: "ai.gftd.apps.maps.spotSearch", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/spotSearch.bpmn", writeTableAllowlist: "" },
  { op: "spotRecommend", processId: "maps_geography_spotRecommend", nsid: "ai.gftd.apps.maps.spotRecommend", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/spotRecommend.bpmn", writeTableAllowlist: "" },
  { op: "registerRiver", processId: "maps_geography_registerRiver", nsid: "ai.gftd.apps.maps.registerRiver", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerRiver.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listRivers", processId: "maps_geography_listRivers", nsid: "ai.gftd.apps.maps.listRivers", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listRivers.bpmn", writeTableAllowlist: "" },
  { op: "registerLake", processId: "maps_geography_registerLake", nsid: "ai.gftd.apps.maps.registerLake", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerLake.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listLakes", processId: "maps_geography_listLakes", nsid: "ai.gftd.apps.maps.listLakes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listLakes.bpmn", writeTableAllowlist: "" },
  { op: "registerCoastline", processId: "maps_geography_registerCoastline", nsid: "ai.gftd.apps.maps.registerCoastline", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerCoastline.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listCoastlines", processId: "maps_geography_listCoastlines", nsid: "ai.gftd.apps.maps.listCoastlines", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listCoastlines.bpmn", writeTableAllowlist: "" },
  { op: "registerMountain", processId: "maps_geography_registerMountain", nsid: "ai.gftd.apps.maps.registerMountain", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerMountain.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listMountains", processId: "maps_geography_listMountains", nsid: "ai.gftd.apps.maps.listMountains", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listMountains.bpmn", writeTableAllowlist: "" },
  { op: "registerMaritimeZone", processId: "maps_geography_registerMaritimeZone", nsid: "ai.gftd.apps.maps.registerMaritimeZone", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerMaritimeZone.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listMaritimeZones", processId: "maps_geography_listMaritimeZones", nsid: "ai.gftd.apps.maps.listMaritimeZones", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listMaritimeZones.bpmn", writeTableAllowlist: "" },
  { op: "registerAdminArea", processId: "maps_geography_registerAdminArea", nsid: "ai.gftd.apps.maps.registerAdminArea", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/registerAdminArea.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listAdminAreas", processId: "maps_geography_listAdminAreas", nsid: "ai.gftd.apps.maps.listAdminAreas", sourcePath: "00-contracts/bpmn/ai/gftd/maps/geography/listAdminAreas.bpmn", writeTableAllowlist: "" },
  { op: "registerAircraft", processId: "maps_transport_extra_registerAircraft", nsid: "ai.gftd.apps.maps.registerAircraft", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerAircraft.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "upsertFlightOperation", processId: "maps_transport_extra_upsertFlightOperation", nsid: "ai.gftd.apps.maps.upsertFlightOperation", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/upsertFlightOperation.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listFlightOperations", processId: "maps_transport_extra_listFlightOperations", nsid: "ai.gftd.apps.maps.listFlightOperations", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listFlightOperations.bpmn", writeTableAllowlist: "" },
  { op: "registerWaterway", processId: "maps_transport_extra_registerWaterway", nsid: "ai.gftd.apps.maps.registerWaterway", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerWaterway.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listWaterways", processId: "maps_transport_extra_listWaterways", nsid: "ai.gftd.apps.maps.listWaterways", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listWaterways.bpmn", writeTableAllowlist: "" },
  { op: "registerPort", processId: "maps_transport_extra_registerPort", nsid: "ai.gftd.apps.maps.registerPort", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerPort.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listPorts", processId: "maps_transport_extra_listPorts", nsid: "ai.gftd.apps.maps.listPorts", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listPorts.bpmn", writeTableAllowlist: "" },
  { op: "registerAirport", processId: "maps_transport_extra_registerAirport", nsid: "ai.gftd.apps.maps.registerAirport", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerAirport.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listAirports", processId: "maps_transport_extra_listAirports", nsid: "ai.gftd.apps.maps.listAirports", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listAirports.bpmn", writeTableAllowlist: "" },
  { op: "registerStation", processId: "maps_transport_extra_registerStation", nsid: "ai.gftd.apps.maps.registerStation", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerStation.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listStations", processId: "maps_transport_extra_listStations", nsid: "ai.gftd.apps.maps.listStations", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listStations.bpmn", writeTableAllowlist: "" },
  { op: "registerBusStop", processId: "maps_transport_extra_registerBusStop", nsid: "ai.gftd.apps.maps.registerBusStop", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerBusStop.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listBusStops", processId: "maps_transport_extra_listBusStops", nsid: "ai.gftd.apps.maps.listBusStops", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listBusStops.bpmn", writeTableAllowlist: "" },
  { op: "registerParking", processId: "maps_transport_extra_registerParking", nsid: "ai.gftd.apps.maps.registerParking", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerParking.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listParkings", processId: "maps_transport_extra_listParkings", nsid: "ai.gftd.apps.maps.listParkings", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listParkings.bpmn", writeTableAllowlist: "" },
  { op: "registerEvCharger", processId: "maps_transport_extra_registerEvCharger", nsid: "ai.gftd.apps.maps.registerEvCharger", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/registerEvCharger.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listEvChargers", processId: "maps_transport_extra_listEvChargers", nsid: "ai.gftd.apps.maps.listEvChargers", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listEvChargers.bpmn", writeTableAllowlist: "" },
  { op: "upsertFlightOffer", processId: "maps_transport_extra_upsertFlightOffer", nsid: "ai.gftd.apps.maps.upsertFlightOffer", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/upsertFlightOffer.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listFlightOffers", processId: "maps_transport_extra_listFlightOffers", nsid: "ai.gftd.apps.maps.listFlightOffers", sourcePath: "00-contracts/bpmn/ai/gftd/maps/transport-extra/listFlightOffers.bpmn", writeTableAllowlist: "" },
  { op: "registerBuilding", processId: "maps_twin_sensor_sim_registerBuilding", nsid: "ai.gftd.apps.maps.registerBuilding", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/registerBuilding.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listBuildings", processId: "maps_twin_sensor_sim_listBuildings", nsid: "ai.gftd.apps.maps.listBuildings", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/listBuildings.bpmn", writeTableAllowlist: "" },
  { op: "getBuilding", processId: "maps_twin_sensor_sim_getBuilding", nsid: "ai.gftd.apps.maps.getBuilding", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/getBuilding.bpmn", writeTableAllowlist: "" },
  { op: "registerBuildingFloor", processId: "maps_twin_sensor_sim_registerBuildingFloor", nsid: "ai.gftd.apps.maps.registerBuildingFloor", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/registerBuildingFloor.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "registerAsset", processId: "maps_twin_sensor_sim_registerAsset", nsid: "ai.gftd.apps.maps.registerAsset", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/registerAsset.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listAssets", processId: "maps_twin_sensor_sim_listAssets", nsid: "ai.gftd.apps.maps.listAssets", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/listAssets.bpmn", writeTableAllowlist: "" },
  { op: "deviceBind", processId: "maps_twin_sensor_sim_deviceBind", nsid: "ai.gftd.apps.maps.deviceBind", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/deviceBind.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listDevices", processId: "maps_twin_sensor_sim_listDevices", nsid: "ai.gftd.apps.maps.listDevices", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/listDevices.bpmn", writeTableAllowlist: "" },
  { op: "twinStateUpdate", processId: "maps_twin_sensor_sim_twinStateUpdate", nsid: "ai.gftd.apps.maps.twinStateUpdate", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/twinStateUpdate.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "twinStateGet", processId: "maps_twin_sensor_sim_twinStateGet", nsid: "ai.gftd.apps.maps.twinStateGet", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/twinStateGet.bpmn", writeTableAllowlist: "" },
  { op: "occupancyUpdate", processId: "maps_twin_sensor_sim_occupancyUpdate", nsid: "ai.gftd.apps.maps.occupancyUpdate", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/occupancyUpdate.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "registerSensor", processId: "maps_twin_sensor_sim_registerSensor", nsid: "ai.gftd.apps.maps.registerSensor", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/registerSensor.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listSensors", processId: "maps_twin_sensor_sim_listSensors", nsid: "ai.gftd.apps.maps.listSensors", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/listSensors.bpmn", writeTableAllowlist: "" },
  { op: "sensorIngest", processId: "maps_twin_sensor_sim_sensorIngest", nsid: "ai.gftd.apps.maps.sensorIngest", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/sensorIngest.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "sensorQuery", processId: "maps_twin_sensor_sim_sensorQuery", nsid: "ai.gftd.apps.maps.sensorQuery", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/sensorQuery.bpmn", writeTableAllowlist: "" },
  { op: "sensorLatest", processId: "maps_twin_sensor_sim_sensorLatest", nsid: "ai.gftd.apps.maps.sensorLatest", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/sensorLatest.bpmn", writeTableAllowlist: "" },
  { op: "sensorAlertSet", processId: "maps_twin_sensor_sim_sensorAlertSet", nsid: "ai.gftd.apps.maps.sensorAlertSet", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/sensorAlertSet.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listSensorAlerts", processId: "maps_twin_sensor_sim_listSensorAlerts", nsid: "ai.gftd.apps.maps.listSensorAlerts", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/listSensorAlerts.bpmn", writeTableAllowlist: "" },
  { op: "simulationCreate", processId: "maps_twin_sensor_sim_simulationCreate", nsid: "ai.gftd.apps.maps.simulationCreate", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/simulationCreate.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "simulationRun", processId: "maps_twin_sensor_sim_simulationRun", nsid: "ai.gftd.apps.maps.simulationRun", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/simulationRun.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "simulationResult", processId: "maps_twin_sensor_sim_simulationResult", nsid: "ai.gftd.apps.maps.simulationResult", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/simulationResult.bpmn", writeTableAllowlist: "" },
  { op: "forecastGet", processId: "maps_twin_sensor_sim_forecastGet", nsid: "ai.gftd.apps.maps.forecastGet", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/forecastGet.bpmn", writeTableAllowlist: "" },
  { op: "healthAssess", processId: "maps_twin_sensor_sim_healthAssess", nsid: "ai.gftd.apps.maps.healthAssess", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/healthAssess.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "maintenancePlan", processId: "maps_twin_sensor_sim_maintenancePlan", nsid: "ai.gftd.apps.maps.maintenancePlan", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/maintenancePlan.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "worldBeliefUpdate", processId: "maps_twin_sensor_sim_worldBeliefUpdate", nsid: "ai.gftd.apps.maps.worldBeliefUpdate", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/worldBeliefUpdate.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "worldBeliefGet", processId: "maps_twin_sensor_sim_worldBeliefGet", nsid: "ai.gftd.apps.maps.worldBeliefGet", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/worldBeliefGet.bpmn", writeTableAllowlist: "" },
  { op: "latentWorldModelRun", processId: "maps_twin_sensor_sim_latentWorldModelRun", nsid: "ai.gftd.apps.maps.latentWorldModelRun", sourcePath: "00-contracts/bpmn/ai/gftd/maps/twin-sensor-sim/latentWorldModelRun.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "spatialEventRecord", processId: "maps_spatiotemporal_spatialEventRecord", nsid: "ai.gftd.apps.maps.spatialEventRecord", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialEventRecord.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "spatialEventQuery", processId: "maps_spatiotemporal_spatialEventQuery", nsid: "ai.gftd.apps.maps.spatialEventQuery", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialEventQuery.bpmn", writeTableAllowlist: "" },
  { op: "spatialVersionRecord", processId: "maps_spatiotemporal_spatialVersionRecord", nsid: "ai.gftd.apps.maps.spatialVersionRecord", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialVersionRecord.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "spatialVersionQuery", processId: "maps_spatiotemporal_spatialVersionQuery", nsid: "ai.gftd.apps.maps.spatialVersionQuery", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialVersionQuery.bpmn", writeTableAllowlist: "" },
  { op: "spatialRelationWrite", processId: "maps_spatiotemporal_spatialRelationWrite", nsid: "ai.gftd.apps.maps.spatialRelationWrite", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialRelationWrite.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "spatialRelationQuery", processId: "maps_spatiotemporal_spatialRelationQuery", nsid: "ai.gftd.apps.maps.spatialRelationQuery", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialRelationQuery.bpmn", writeTableAllowlist: "" },
  { op: "timeline", processId: "maps_spatiotemporal_timeline", nsid: "ai.gftd.apps.maps.timeline", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/timeline.bpmn", writeTableAllowlist: "" },
  { op: "spatialDiff", processId: "maps_spatiotemporal_spatialDiff", nsid: "ai.gftd.apps.maps.spatialDiff", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/spatialDiff.bpmn", writeTableAllowlist: "" },
  { op: "displayLayerDefine", processId: "maps_spatiotemporal_displayLayerDefine", nsid: "ai.gftd.apps.maps.displayLayerDefine", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/displayLayerDefine.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listDisplayLayers", processId: "maps_spatiotemporal_listDisplayLayers", nsid: "ai.gftd.apps.maps.listDisplayLayers", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/listDisplayLayers.bpmn", writeTableAllowlist: "" },
  { op: "getDashboard", processId: "maps_spatiotemporal_getDashboard", nsid: "ai.gftd.apps.maps.getDashboard", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/getDashboard.bpmn", writeTableAllowlist: "" },
  { op: "actorLocations", processId: "maps_spatiotemporal_actorLocations", nsid: "ai.gftd.apps.maps.actorLocations", sourcePath: "00-contracts/bpmn/ai/gftd/maps/spatiotemporal/actorLocations.bpmn", writeTableAllowlist: "" },
  { op: "listPostLocations", processId: "maps_registry_media_listPostLocations", nsid: "ai.gftd.apps.maps.listPostLocations", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listPostLocations.bpmn", writeTableAllowlist: "" },
  { op: "mapralyImportPoi", processId: "maps_registry_media_mapralyImportPoi", nsid: "ai.gftd.apps.maps.mapralyImportPoi", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/mapralyImportPoi.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "mapralyListPois", processId: "maps_registry_media_mapralyListPois", nsid: "ai.gftd.apps.maps.mapralyListPois", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/mapralyListPois.bpmn", writeTableAllowlist: "" },
  { op: "visionImportEntities", processId: "maps_registry_media_visionImportEntities", nsid: "ai.gftd.apps.maps.visionImportEntities", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/visionImportEntities.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listVisionResults", processId: "maps_registry_media_listVisionResults", nsid: "ai.gftd.apps.maps.listVisionResults", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listVisionResults.bpmn", writeTableAllowlist: "" },
  { op: "satelliteImportScene", processId: "maps_registry_media_satelliteImportScene", nsid: "ai.gftd.apps.maps.satelliteImportScene", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/satelliteImportScene.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listSatelliteScenes", processId: "maps_registry_media_listSatelliteScenes", nsid: "ai.gftd.apps.maps.listSatelliteScenes", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listSatelliteScenes.bpmn", writeTableAllowlist: "" },
  { op: "listSatelliteSources", processId: "maps_registry_media_listSatelliteSources", nsid: "ai.gftd.apps.maps.listSatelliteSources", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listSatelliteSources.bpmn", writeTableAllowlist: "" },
  { op: "listGeoDomains", processId: "maps_registry_media_listGeoDomains", nsid: "ai.gftd.apps.maps.listGeoDomains", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listGeoDomains.bpmn", writeTableAllowlist: "" },
  { op: "listWebCrawlGeoEntities", processId: "maps_registry_media_listWebCrawlGeoEntities", nsid: "ai.gftd.apps.maps.listWebCrawlGeoEntities", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listWebCrawlGeoEntities.bpmn", writeTableAllowlist: "" },
  { op: "registerLegalEntity", processId: "maps_registry_media_registerLegalEntity", nsid: "ai.gftd.apps.maps.registerLegalEntity", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerLegalEntity.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listLegalEntities", processId: "maps_registry_media_listLegalEntities", nsid: "ai.gftd.apps.maps.listLegalEntities", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listLegalEntities.bpmn", writeTableAllowlist: "" },
  { op: "registerOperator", processId: "maps_registry_media_registerOperator", nsid: "ai.gftd.apps.maps.registerOperator", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerOperator.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listOperators", processId: "maps_registry_media_listOperators", nsid: "ai.gftd.apps.maps.listOperators", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listOperators.bpmn", writeTableAllowlist: "" },
  { op: "registerPropertyOwner", processId: "maps_registry_media_registerPropertyOwner", nsid: "ai.gftd.apps.maps.registerPropertyOwner", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerPropertyOwner.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listPropertyOwners", processId: "maps_registry_media_listPropertyOwners", nsid: "ai.gftd.apps.maps.listPropertyOwners", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listPropertyOwners.bpmn", writeTableAllowlist: "" },
  { op: "registerLandRegistry", processId: "maps_registry_media_registerLandRegistry", nsid: "ai.gftd.apps.maps.registerLandRegistry", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerLandRegistry.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listLandRegistries", processId: "maps_registry_media_listLandRegistries", nsid: "ai.gftd.apps.maps.listLandRegistries", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listLandRegistries.bpmn", writeTableAllowlist: "" },
  { op: "registerPropertyRegistry", processId: "maps_registry_media_registerPropertyRegistry", nsid: "ai.gftd.apps.maps.registerPropertyRegistry", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerPropertyRegistry.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listPropertyRegistries", processId: "maps_registry_media_listPropertyRegistries", nsid: "ai.gftd.apps.maps.listPropertyRegistries", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listPropertyRegistries.bpmn", writeTableAllowlist: "" },
  { op: "registerBusinessRegistry", processId: "maps_registry_media_registerBusinessRegistry", nsid: "ai.gftd.apps.maps.registerBusinessRegistry", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerBusinessRegistry.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listBusinessRegistries", processId: "maps_registry_media_listBusinessRegistries", nsid: "ai.gftd.apps.maps.listBusinessRegistries", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listBusinessRegistries.bpmn", writeTableAllowlist: "" },
  { op: "registerConstructionPermit", processId: "maps_registry_media_registerConstructionPermit", nsid: "ai.gftd.apps.maps.registerConstructionPermit", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerConstructionPermit.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listConstructionPermits", processId: "maps_registry_media_listConstructionPermits", nsid: "ai.gftd.apps.maps.listConstructionPermits", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listConstructionPermits.bpmn", writeTableAllowlist: "" },
  { op: "registerOperatingLicense", processId: "maps_registry_media_registerOperatingLicense", nsid: "ai.gftd.apps.maps.registerOperatingLicense", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerOperatingLicense.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listOperatingLicenses", processId: "maps_registry_media_listOperatingLicenses", nsid: "ai.gftd.apps.maps.listOperatingLicenses", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listOperatingLicenses.bpmn", writeTableAllowlist: "" },
  { op: "registerZoningRecord", processId: "maps_registry_media_registerZoningRecord", nsid: "ai.gftd.apps.maps.registerZoningRecord", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerZoningRecord.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "listZoningRecords", processId: "maps_registry_media_listZoningRecords", nsid: "ai.gftd.apps.maps.listZoningRecords", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/listZoningRecords.bpmn", writeTableAllowlist: "" },
  { op: "registerOwnership", processId: "maps_registry_media_registerOwnership", nsid: "ai.gftd.apps.maps.registerOwnership", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/registerOwnership.bpmn", writeTableAllowlist: "vertex_spatial" },
  { op: "ownershipChain", processId: "maps_registry_media_ownershipChain", nsid: "ai.gftd.apps.maps.ownershipChain", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/ownershipChain.bpmn", writeTableAllowlist: "" },
  { op: "entityHistory", processId: "maps_registry_media_entityHistory", nsid: "ai.gftd.apps.maps.entityHistory", sourcePath: "00-contracts/bpmn/ai/gftd/maps/registry-media/entityHistory.bpmn", writeTableAllowlist: "" },
];

const slug = (s: Seed) => s.op.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-collection-${slug(s)}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/maps-collection-${slug(s)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, s.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path,
         status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath},
             'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})
    `.execute(db);
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
         write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,
         actor_id, actor_did, org_did)
      SELECT ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1, 30000,
             ${s.writeTableAllowlist}, 'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid},
             ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
