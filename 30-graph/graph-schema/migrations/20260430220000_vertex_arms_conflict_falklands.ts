// tier: B/C (open defence history, public interstate arms-transfer graph)
//
// Arms Phase 2 - interstate conflict, arms-transfer dependency, and event
// chronology. Seeds the 1982 Falklands/Malvinas case because it is the
// canonical example where French-origin missiles/aircraft became an operational
// dependency inside a UK-Argentina conflict.
import type { Kysely } from "kysely";
import { sql } from "kysely";

const ownerDid = "did:web:arms.gftd.ai";
const createdAt = "2026-04-30T22:00:00+09:00";
const actorId = "sys.schema.seed.arms.falklands";
const orgDid = "did:web:arms.gftd.ai";

const conflictId = "arms:conflict:falklands-malvinas-1982";
const transferSuperEtendardId = "arms:transfer:fra-arg-super-etendard-exocet-1981";
const transferEmbargoId = "arms:transfer:fra-arg-arms-embargo-1982";

const actors = [
  {
    actorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    role: "belligerent",
    side: "united-kingdom",
    countryIso3: "GBR",
    note: "United Kingdom task force retook the Falkland Islands and South Georgia.",
  },
  {
    actorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    role: "belligerent",
    side: "argentina",
    countryIso3: "ARG",
    note: "Argentina invaded and occupied the islands, then surrendered on 1982-06-14.",
  },
  {
    actorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr",
    role: "supplier_then_embargoing_state",
    side: "third-party-supplier",
    countryIso3: "FRA",
    note: "France supplied Super Etendard aircraft and AM39 Exocet missiles before the war, then imposed an embargo during the conflict.",
  },
];

const transfers = [
  {
    vertexId: transferSuperEtendardId,
    transferKind: "prewar_export",
    supplierActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr",
    supplierCountryIso3: "FRA",
    recipientActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    recipientCountryIso3: "ARG",
    equipmentName: "Dassault-Breguet Super Etendard + AM39 Exocet",
    equipmentType: "strike_aircraft_and_anti_ship_missile",
    weaponFamily: "Exocet",
    quantityOrdered: 14,
    quantityDelivered: 5,
    quantityMissilesDelivered: 5,
    contractAt: "1979",
    deliveryStartAt: "1981-08",
    deliveryEndAt: "1981-11",
    status: "delivered_prewar_first_batch",
    complianceFrame: "prewar_contract_later_embargoed",
    sourceUri: "https://www.usni.org/magazines/proceedings/1983/may/malvinas-campaign",
    notes: "USNI reports five aircraft and five missiles shipped from France to Argentina between August and November 1981.",
  },
  {
    vertexId: transferEmbargoId,
    transferKind: "wartime_embargo",
    supplierActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr",
    supplierCountryIso3: "FRA",
    recipientActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    recipientCountryIso3: "ARG",
    equipmentName: "Further Super Etendard and Exocet deliveries",
    equipmentType: "arms_embargo",
    weaponFamily: "Exocet",
    quantityOrdered: 9,
    quantityDelivered: 0,
    quantityMissilesDelivered: 0,
    contractAt: "1979",
    deliveryStartAt: "1982-04",
    deliveryEndAt: "1982-08",
    status: "halted_during_conflict",
    complianceFrame: "solidarity_embargo_after_invasion",
    sourceUri: "https://www.upi.com/Archives/1982/11/20/French-resume-shipping-exocet-missiles-to-Argentina/8561406616400/",
    notes: "UPI reported France had imposed an arms-shipment embargo in solidarity with Britain, later lifting it for old prewar contracts.",
  },
];

const events = [
  {
    vertexId: "arms:event:falklands-1833-british-control",
    occurredAt: "1833",
    eventKind: "background_sovereignty_dispute",
    title: "Britain reasserts control over the Falkland Islands",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "FK",
    weaponSystem: "",
    outcome: "long_running_sovereignty_dispute",
    impact: "Argentina maintained a sovereignty claim; Britain rejected it.",
    sourceUri: "https://www.britannica.com/event/Falkland-Islands-War",
  },
  {
    vertexId: "arms:event:falklands-1976-south-sandwich-presence",
    occurredAt: "1976",
    eventKind: "background_presence",
    title: "Argentina establishes an unauthorized presence in the South Sandwich Islands",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "GS",
    weaponSystem: "",
    outcome: "unopposed_presence",
    impact: "Prewar friction over associated South Atlantic dependencies increased.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1981-france-delivery",
    occurredAt: "1981-11",
    eventKind: "arms_delivery",
    title: "France delivers first Super Etendard and Exocet batch to Argentina",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr",
    opposingActorVid: "",
    locationCode: "AR",
    weaponSystem: "Super Etendard; AM39 Exocet",
    outcome: "argentine_naval_air_strike_capability",
    impact: "Argentina entered the conflict with a small but high-leverage anti-ship missile capability.",
    sourceUri: "https://www.usni.org/magazines/proceedings/1983/may/malvinas-campaign",
  },
  {
    vertexId: "arms:event:falklands-1982-03-19-south-georgia",
    occurredAt: "1982-03-19",
    eventKind: "trigger_dispute",
    title: "South Georgia flag incident accelerates crisis timetable",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "GS",
    weaponSystem: "",
    outcome: "naval_mobilization",
    impact: "The incident shortened the timetable before the Argentine invasion.",
    sourceUri: "https://www.britannica.com/event/Falkland-Islands-War",
  },
  {
    vertexId: "arms:event:falklands-1982-04-02-invasion",
    occurredAt: "1982-04-02",
    eventKind: "invasion",
    title: "Argentina invades the Falkland Islands",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "FK",
    weaponSystem: "amphibious_force",
    outcome: "argentine_occupation",
    impact: "The invasion started the 74-day war.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-04-03-south-georgia",
    occurredAt: "1982-04-03",
    eventKind: "occupation_expands",
    title: "Argentina occupies South Georgia",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "GS",
    weaponSystem: "naval_infantry",
    outcome: "argentine_occupation",
    impact: "The conflict extended to associated South Atlantic dependencies.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-04-05-task-force",
    occurredAt: "1982-04-05",
    eventKind: "task_force_deployment",
    title: "British carrier task force sails south",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "GB",
    weaponSystem: "naval_task_force",
    outcome: "operation_corporate",
    impact: "Britain committed naval, air, and ground forces to retake the islands.",
    sourceUri: "https://www.britannica.com/event/Falkland-Islands-War",
  },
  {
    vertexId: "arms:event:falklands-1982-04-france-embargo",
    occurredAt: "1982-04",
    eventKind: "export_control",
    title: "France halts further arms shipments to Argentina during conflict",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:fr",
    opposingActorVid: "",
    locationCode: "FR",
    weaponSystem: "Super Etendard; AM39 Exocet",
    outcome: "remaining_deliveries_halted",
    impact: "Argentina fought with only the already delivered first batch of the French aircraft-missile system.",
    sourceUri: "https://www.upi.com/Archives/1982/11/20/French-resume-shipping-exocet-missiles-to-Argentina/8561406616400/",
  },
  {
    vertexId: "arms:event:falklands-1982-04-25-south-georgia-retaken",
    occurredAt: "1982-04-25",
    eventKind: "recapture",
    title: "Operation Paraquet returns South Georgia to British control",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "GS",
    weaponSystem: "naval_task_force",
    outcome: "british_control_restored",
    impact: "Argentine forces in South Georgia surrendered before the main Falklands land campaign.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-04-30-exclusion-zone",
    occurredAt: "1982-04-30",
    eventKind: "maritime_exclusion_zone",
    title: "Britain imposes a 200-mile Total Exclusion Zone",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "FK",
    weaponSystem: "naval_blockade",
    outcome: "exclusion_zone_active",
    impact: "The maritime and air operating environment around the islands changed.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-05-02-belgrano",
    occurredAt: "1982-05-02",
    eventKind: "naval_sinking",
    title: "HMS Conqueror sinks ARA General Belgrano",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "FK",
    weaponSystem: "submarine_torpedo",
    outcome: "argentine_cruiser_sunk",
    impact: "More than 300 Argentine crew were lost and naval escalation sharpened.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-05-04-sheffield-exocet",
    occurredAt: "1982-05-04",
    eventKind: "missile_strike",
    title: "AM39 Exocet strike destroys HMS Sheffield",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "FK",
    weaponSystem: "Super Etendard; AM39 Exocet",
    outcome: "hms_sheffield_destroyed",
    impact: "The French-origin aircraft-missile dependency became operationally decisive; 20 were killed.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-05-21-san-carlos",
    occurredAt: "1982-05-21",
    eventKind: "amphibious_landing",
    title: "British troops land at San Carlos and Ajax Bay",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "FK",
    weaponSystem: "amphibious_landing_force",
    outcome: "bridgehead_established",
    impact: "The land campaign on East Falkland began.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-05-25-atlantic-conveyor-exocet",
    occurredAt: "1982-05-25",
    eventKind: "missile_strike",
    title: "Exocet strike hits SS Atlantic Conveyor",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "FK",
    weaponSystem: "Super Etendard; AM39 Exocet",
    outcome: "atlantic_conveyor_lost",
    impact: "Loss of transport and helicopter capacity affected the British advance.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-05-29-goose-green",
    occurredAt: "1982-05-29",
    eventKind: "land_battle",
    title: "British forces take Goose Green",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    locationCode: "FK",
    weaponSystem: "infantry",
    outcome: "british_capture",
    impact: "First settlement captured by British ground forces.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
  {
    vertexId: "arms:event:falklands-1982-06-14-surrender",
    occurredAt: "1982-06-14",
    eventKind: "surrender",
    title: "Argentine forces surrender in the Falkland Islands",
    primaryActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:ar",
    opposingActorVid: "did:web:uqpel6i6.gftd.ai:geo:iso3166-1:gb",
    locationCode: "FK",
    weaponSystem: "",
    outcome: "british_control_restored",
    impact: "The 74-day war ended with the Falklands back under British control.",
    sourceUri: "https://www.iwm.org.uk/history/cold-war/falklands-conflict",
  },
];

const dependencies = [
  ["arms:event:falklands-1833-british-control", "arms:event:falklands-1982-04-02-invasion", "sovereignty_claim_background"],
  ["arms:event:falklands-1976-south-sandwich-presence", "arms:event:falklands-1982-04-03-south-georgia", "dependency_dispute_background"],
  ["arms:event:falklands-1981-france-delivery", "arms:event:falklands-1982-05-04-sheffield-exocet", "weapon_system_enabled"],
  ["arms:event:falklands-1981-france-delivery", "arms:event:falklands-1982-05-25-atlantic-conveyor-exocet", "weapon_system_enabled"],
  ["arms:event:falklands-1982-03-19-south-georgia", "arms:event:falklands-1982-04-02-invasion", "crisis_accelerator"],
  ["arms:event:falklands-1982-04-02-invasion", "arms:event:falklands-1982-04-05-task-force", "military_response"],
  ["arms:event:falklands-1982-04-05-task-force", "arms:event:falklands-1982-04-30-exclusion-zone", "operational_precondition"],
  ["arms:event:falklands-1982-04-30-exclusion-zone", "arms:event:falklands-1982-05-02-belgrano", "operational_context"],
  ["arms:event:falklands-1982-05-04-sheffield-exocet", "arms:event:falklands-1982-05-21-san-carlos", "threat_environment"],
  ["arms:event:falklands-1982-05-21-san-carlos", "arms:event:falklands-1982-05-29-goose-green", "campaign_sequence"],
  ["arms:event:falklands-1982-05-25-atlantic-conveyor-exocet", "arms:event:falklands-1982-06-14-surrender", "logistics_constraint"],
  ["arms:event:falklands-1982-05-29-goose-green", "arms:event:falklands-1982-06-14-surrender", "campaign_sequence"],
];

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_arms_conflict (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      canonical_name        varchar NOT NULL,
      alternate_names       varchar,
      conflict_kind         varchar NOT NULL,
      start_at              varchar,
      end_at                varchar,
      status                varchar NOT NULL,
      primary_location_code varchar,
      sovereignty_issue     varchar,
      summary               varchar,
      source_uri            varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar,
      actor_did             varchar,
      org_did               varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_arms_conflict_dates ON vertex_arms_conflict (start_at, end_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_arms_conflict_location ON vertex_arms_conflict (primary_location_code)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_arms_transfer (
      vertex_id                  varchar PRIMARY KEY,
      _seq                       bigint,
      created_date               date,
      sensitivity_ord            int,
      owner_did                  varchar,
      transfer_kind              varchar NOT NULL,
      supplier_actor_vid         varchar NOT NULL,
      supplier_country_iso3      varchar NOT NULL,
      recipient_actor_vid        varchar NOT NULL,
      recipient_country_iso3     varchar NOT NULL,
      equipment_name             varchar NOT NULL,
      equipment_type             varchar NOT NULL,
      weapon_family              varchar,
      quantity_ordered           int,
      quantity_delivered         int,
      quantity_missiles_delivered int,
      contract_at                varchar,
      delivery_start_at          varchar,
      delivery_end_at            varchar,
      status                     varchar NOT NULL,
      compliance_frame           varchar,
      source_uri                 varchar,
      notes                      varchar,
      created_at                 varchar,
      org_id                     varchar,
      user_id                    varchar,
      actor_id                   varchar,
      actor_did                  varchar,
      org_did                    varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_arms_transfer_supplier_recipient ON vertex_arms_transfer (supplier_country_iso3, recipient_country_iso3)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_arms_transfer_equipment ON vertex_arms_transfer (weapon_family, equipment_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_arms_transfer_dates ON vertex_arms_transfer (delivery_start_at, delivery_end_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_arms_conflict_event (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      conflict_vid       varchar NOT NULL,
      occurred_at        varchar NOT NULL,
      event_kind         varchar NOT NULL,
      title              varchar NOT NULL,
      primary_actor_vid  varchar,
      opposing_actor_vid varchar,
      location_code      varchar,
      weapon_system      varchar,
      outcome            varchar,
      impact             varchar,
      source_uri         varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar,
      actor_did          varchar,
      org_did            varchar
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_arms_conflict_event_conflict_time ON vertex_arms_conflict_event (conflict_vid, occurred_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_arms_conflict_event_kind ON vertex_arms_conflict_event (event_kind, occurred_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_arms_conflict_event_actor ON vertex_arms_conflict_event (primary_actor_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_arms_conflict_actor (
      src              varchar NOT NULL,
      dst              varchar NOT NULL,
      rel              varchar NOT NULL,
      side             varchar,
      country_iso3     varchar,
      note             varchar,
      created_at       varchar,
      owner_did         varchar,
      sensitivity_ord  int,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar,
      actor_did        varchar,
      org_did          varchar,
      PRIMARY KEY (src, dst, rel)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_arms_conflict_actor_dst ON edge_arms_conflict_actor (dst)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_arms_transfer_to_conflict (
      src              varchar NOT NULL,
      dst              varchar NOT NULL,
      rel              varchar NOT NULL,
      dependency_kind  varchar,
      created_at       varchar,
      owner_did         varchar,
      sensitivity_ord  int,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar,
      actor_did        varchar,
      org_did          varchar,
      PRIMARY KEY (src, dst, rel)
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_arms_event_dependency (
      src              varchar NOT NULL,
      dst              varchar NOT NULL,
      rel              varchar NOT NULL,
      dependency_kind  varchar,
      created_at       varchar,
      owner_did         varchar,
      sensitivity_ord  int,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar,
      actor_did        varchar,
      org_did          varchar,
      PRIMARY KEY (src, dst, rel)
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_arms_event_dependency_dst ON edge_arms_event_dependency (dst)`.execute(db);

  await sql`
    INSERT INTO vertex_arms_conflict (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did,
      canonical_name, alternate_names, conflict_kind, start_at, end_at, status,
      primary_location_code, sovereignty_issue, summary, source_uri,
      created_at, org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${conflictId}, NULL, CAST('2026-04-30' AS date), 1, ${ownerDid},
      'Falklands/Malvinas War 1982',
      'Falkland Islands War; Malvinas War; South Atlantic War',
      'interstate_territorial_war',
      '1982-04-02',
      '1982-06-14',
      'ended',
      'FK',
      'United Kingdom sovereignty vs Argentina claim over Falkland Islands, South Georgia and South Sandwich Islands',
      'Short undeclared 1982 war between Argentina and the United Kingdom. The arms-transfer dependency of interest is France-to-Argentina Super Etendard aircraft and AM39 Exocet missiles delivered before the war, followed by a wartime embargo.',
      'https://www.iwm.org.uk/history/cold-war/falklands-conflict',
      ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, ${orgDid}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict WHERE vertex_id = ${conflictId})
  `.execute(db);

  for (const actor of actors) {
    await sql`
      INSERT INTO edge_arms_conflict_actor (
        src, dst, rel, side, country_iso3, note, created_at,
        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${conflictId}, ${actor.actorVid}, ${actor.role}, ${actor.side}, ${actor.countryIso3}, ${actor.note}, ${createdAt},
        ${ownerDid}, 1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, ${orgDid}
      WHERE NOT EXISTS (
        SELECT 1 FROM edge_arms_conflict_actor
        WHERE src = ${conflictId} AND dst = ${actor.actorVid} AND rel = ${actor.role}
      )
    `.execute(db);
  }

  for (const transfer of transfers) {
    await sql`
      INSERT INTO vertex_arms_transfer (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        transfer_kind, supplier_actor_vid, supplier_country_iso3, recipient_actor_vid,
        recipient_country_iso3, equipment_name, equipment_type, weapon_family,
        quantity_ordered, quantity_delivered, quantity_missiles_delivered,
        contract_at, delivery_start_at, delivery_end_at, status, compliance_frame,
        source_uri, notes, created_at, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${transfer.vertexId}, NULL, CAST('2026-04-30' AS date), 1, ${ownerDid},
        ${transfer.transferKind}, ${transfer.supplierActorVid}, ${transfer.supplierCountryIso3}, ${transfer.recipientActorVid},
        ${transfer.recipientCountryIso3}, ${transfer.equipmentName}, ${transfer.equipmentType}, ${transfer.weaponFamily},
        CAST(${transfer.quantityOrdered} AS integer), CAST(${transfer.quantityDelivered} AS integer), CAST(${transfer.quantityMissilesDelivered} AS integer),
        ${transfer.contractAt}, ${transfer.deliveryStartAt}, ${transfer.deliveryEndAt}, ${transfer.status}, ${transfer.complianceFrame},
        ${transfer.sourceUri}, ${transfer.notes}, ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, ${orgDid}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_transfer WHERE vertex_id = ${transfer.vertexId})
    `.execute(db);

    await sql`
      INSERT INTO edge_arms_transfer_to_conflict (
        src, dst, rel, dependency_kind, created_at,
        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${transfer.vertexId}, ${conflictId}, 'transfer_context_for', ${transfer.transferKind}, ${createdAt},
        ${ownerDid}, 1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, ${orgDid}
      WHERE NOT EXISTS (
        SELECT 1 FROM edge_arms_transfer_to_conflict
        WHERE src = ${transfer.vertexId} AND dst = ${conflictId} AND rel = 'transfer_context_for'
      )
    `.execute(db);
  }

  for (const event of events) {
    await sql`
      INSERT INTO vertex_arms_conflict_event (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did, conflict_vid,
        occurred_at, event_kind, title, primary_actor_vid, opposing_actor_vid,
        location_code, weapon_system, outcome, impact, source_uri,
        created_at, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${event.vertexId}, NULL, CAST('2026-04-30' AS date), 1, ${ownerDid}, ${conflictId},
        ${event.occurredAt}, ${event.eventKind}, ${event.title}, ${event.primaryActorVid}, ${event.opposingActorVid},
        ${event.locationCode}, ${event.weaponSystem}, ${event.outcome}, ${event.impact}, ${event.sourceUri},
        ${createdAt}, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, ${orgDid}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_arms_conflict_event WHERE vertex_id = ${event.vertexId})
    `.execute(db);
  }

  for (const [src, dst, dependencyKind] of dependencies) {
    await sql`
      INSERT INTO edge_arms_event_dependency (
        src, dst, rel, dependency_kind, created_at,
        owner_did, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${src}, ${dst}, 'precedes_enables_or_constrains', ${dependencyKind}, ${createdAt},
        ${ownerDid}, 1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, ${orgDid}
      WHERE NOT EXISTS (
        SELECT 1 FROM edge_arms_event_dependency
        WHERE src = ${src} AND dst = ${dst} AND rel = 'precedes_enables_or_constrains'
      )
    `.execute(db);
  }

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_arms_event_dependency`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_arms_transfer_to_conflict`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_arms_conflict_actor`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_conflict_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_transfer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_arms_conflict`.execute(db);
}
