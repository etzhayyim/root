CREATE TABLE IF NOT EXISTS vertex_hakkou_ferment (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  input_kind TEXT,
  input_ref TEXT,
  output_vertex_id TEXT,
  output_kind TEXT,
  ethanol_hash TEXT,
  co2_audit_ref TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_kobo_agent (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  parent_did TEXT,
  role TEXT,
  eta REAL,
  stress_score REAL,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_kobo_prion (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  pattern_hash TEXT,
  heritable INTEGER,
  malignant_score REAL,
  content TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_kobo_budding (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  parent_did TEXT,
  child_did TEXT,
  budded_at TEXT,
  prion_count INTEGER,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_kabi_hypha (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  src_agent_did TEXT,
  dst_agent_did TEXT,
  eta REAL,
  flow REAL,
  pruned_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_kabi_anastomosis (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  network_a_did TEXT,
  network_b_did TEXT,
  compatibility_score REAL,
  result TEXT,
  reason TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_kabi_network (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  root_agent_did TEXT,
  hypha_count INTEGER,
  total_flow REAL,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_kinoko_block (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  prev_block_id TEXT,
  block_hash TEXT,
  total_flow REAL,
  participant_count INTEGER,
  eta_min_used REAL,
  block_status TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_houshi_spore (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  origin_agent_did TEXT,
  blob_cbor TEXT,
  revival_key_hint TEXT,
  quorum_n INTEGER,
  germinated_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_houshi_custody (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  custodian_did TEXT,
  custody_confirmed INTEGER,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_koke_fixation (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  input_kind TEXT,
  raw_ref TEXT,
  signal_hash TEXT,
  classification TEXT,
  confidence REAL,
  fixed_at TEXT,
  released_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_koke_flow (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  fixation_id TEXT,
  ferment_id TEXT,
  handoff_kind TEXT,
  handed_off_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_saikin_signal (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  input_kind TEXT,
  raw_ref TEXT,
  signal_hash TEXT,
  probe_source TEXT,
  transferred_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_saikin_colony (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  colony_label TEXT,
  member_count INTEGER,
  formed_at TEXT,
  lysed_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_saikin_transfer (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  signal_id TEXT,
  target_actor_did TEXT,
  transfer_kind TEXT,
  transferred_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_saikin_member (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  colony_id TEXT,
  signal_id TEXT,
  joined_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_ki_absorb (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  source_vertex_id TEXT,
  input_kind TEXT,
  content_hash TEXT,
  absorbed_at TEXT,
  synthesized_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_ki_artifact (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  absorb_id TEXT,
  artifact_kind TEXT,
  synthesis TEXT,
  confidence REAL,
  artifact_hash TEXT,
  bloomed_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS vertex_ki_ring (
  vertex_id TEXT PRIMARY KEY,
  record_id TEXT,
  owner_did TEXT,
  label TEXT,
  status TEXT,
  stream_id TEXT,
  agent_did TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  period TEXT,
  snapshot_count INTEGER,
  ring_at TEXT,
  at_uri TEXT
);

CREATE TABLE IF NOT EXISTS edge_ki_vascular (
  edge_id TEXT PRIMARY KEY,
  src_vid TEXT,
  dst_vid TEXT,
  relation_kind TEXT,
  value_json TEXT,
  created_at TEXT,
  updated_at TEXT,
  owner_did TEXT,
  sensitivity_ord INTEGER NOT NULL DEFAULT 1,
  flow_kind TEXT,
  flow_at TEXT,
  at_uri TEXT
);

        "vertex_hakkou_ferment": f"{prefix}.hakkouFerment",
        "vertex_kobo_agent": f"{prefix}.koboAgent",
        "vertex_kobo_prion": f"{prefix}.koboPrion",
        "edge_kobo_budding": f"{prefix}.koboBudding",
        "edge_kabi_hypha": f"{prefix}.kabiHypha",
        "edge_kabi_anastomosis": f"{prefix}.kabiAnastomosis",
        "vertex_kabi_network": f"{prefix}.kabiNetwork",
        "vertex_kinoko_block": f"{prefix}.kinokoBlock",
        "vertex_houshi_spore": f"{prefix}.houshiSpore",
        "edge_houshi_custody": f"{prefix}.houshiCustody",
        "vertex_koke_fixation": f"{prefix}.kokeFixation",
        "edge_koke_flow": f"{prefix}.kokeFlow",
        "vertex_saikin_signal": f"{prefix}.saikinSignal",
        "vertex_saikin_colony": f"{prefix}.saikinColony",
        "edge_saikin_transfer": f"{prefix}.saikinTransfer",
        "edge_saikin_member": f"{prefix}.saikinMember",
        "vertex_ki_absorb": f"{prefix}.kiAbsorb",
        "vertex_ki_artifact": f"{prefix}.kiArtifact",
        "vertex_ki_ring": f"{prefix}.kiRing",
        "edge_ki_vascular": f"{prefix}.kiVascular",
    "vertex_hakkou_ferment": "put_vertex_hakkou_ferment",
    "vertex_kobo_agent": "put_vertex_kobo_agent",
    "vertex_kobo_prion": "put_vertex_kobo_prion",
    "edge_kobo_budding": "put_edge_kobo_budding",
    "edge_kabi_hypha": "put_edge_kabi_hypha",
    "edge_kabi_anastomosis": "put_edge_kabi_anastomosis",
    "vertex_kabi_network": "put_vertex_kabi_network",
    "vertex_kinoko_block": "put_vertex_kinoko_block",
    "vertex_houshi_spore": "put_vertex_houshi_spore",
    "edge_houshi_custody": "put_edge_houshi_custody",
    "vertex_koke_fixation": "put_vertex_koke_fixation",
    "edge_koke_flow": "put_edge_koke_flow",
    "vertex_saikin_signal": "put_vertex_saikin_signal",
    "vertex_saikin_colony": "put_vertex_saikin_colony",
    "edge_saikin_transfer": "put_edge_saikin_transfer",
    "edge_saikin_member": "put_edge_saikin_member",
    "vertex_ki_absorb": "put_vertex_ki_absorb",
    "vertex_ki_artifact": "put_vertex_ki_artifact",
    "vertex_ki_ring": "put_vertex_ki_ring",
    "edge_ki_vascular": "put_edge_ki_vascular",
    def put_vertex_hakkou_ferment(self, rec: HakkouFermentRecord) -> str:
        row = _row_dict(rec, prefix="hakkou-ferment", key_fields=("agent_did", "created_at"))
        return self._put("vertex_hakkou_ferment", row)

    def put_vertex_kobo_agent(self, rec: KoboAgentRecord) -> str:
        row = _row_dict(rec, prefix="kobo-agent", key_fields=("agent_did", "created_at"))
        return self._put("vertex_kobo_agent", row)

    def put_vertex_kobo_prion(self, rec: KoboPrionRecord) -> str:
        row = _row_dict(rec, prefix="kobo-prion", key_fields=("agent_did", "created_at"))
        return self._put("vertex_kobo_prion", row)

    def put_edge_kobo_budding(self, rec: KoboBuddingRecord) -> str:
        row = _row_dict(rec, prefix="kobo-budding", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_kobo_budding", row)

    def put_edge_kabi_hypha(self, rec: KabiHyphaRecord) -> str:
        row = _row_dict(rec, prefix="kabi-hypha", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_kabi_hypha", row)

    def put_edge_kabi_anastomosis(self, rec: KabiAnastomosisRecord) -> str:
        row = _row_dict(rec, prefix="kabi-anastomosis", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_kabi_anastomosis", row)

    def put_vertex_kabi_network(self, rec: KabiNetworkRecord) -> str:
        row = _row_dict(rec, prefix="kabi-network", key_fields=("agent_did", "created_at"))
        return self._put("vertex_kabi_network", row)

    def put_vertex_kinoko_block(self, rec: KinokoBlockRecord) -> str:
        row = _row_dict(rec, prefix="kinoko-block", key_fields=("agent_did", "created_at"))
        return self._put("vertex_kinoko_block", row)

    def put_vertex_houshi_spore(self, rec: HoushiSporeRecord) -> str:
        row = _row_dict(rec, prefix="houshi-spore", key_fields=("agent_did", "created_at"))
        return self._put("vertex_houshi_spore", row)

    def put_edge_houshi_custody(self, rec: HoushiCustodyRecord) -> str:
        row = _row_dict(rec, prefix="houshi-custody", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_houshi_custody", row)

    def put_vertex_koke_fixation(self, rec: KokeFixationRecord) -> str:
        row = _row_dict(rec, prefix="koke-fixation", key_fields=("agent_did", "created_at"))
        return self._put("vertex_koke_fixation", row)

    def put_edge_koke_flow(self, rec: KokeFlowRecord) -> str:
        row = _row_dict(rec, prefix="koke-flow", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_koke_flow", row)

    def put_vertex_saikin_signal(self, rec: SaikinSignalRecord) -> str:
        row = _row_dict(rec, prefix="saikin-signal", key_fields=("agent_did", "created_at"))
        return self._put("vertex_saikin_signal", row)

    def put_vertex_saikin_colony(self, rec: SaikinColonyRecord) -> str:
        row = _row_dict(rec, prefix="saikin-colony", key_fields=("agent_did", "created_at"))
        return self._put("vertex_saikin_colony", row)

    def put_edge_saikin_transfer(self, rec: SaikinTransferRecord) -> str:
        row = _row_dict(rec, prefix="saikin-transfer", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_saikin_transfer", row)

    def put_edge_saikin_member(self, rec: SaikinMemberRecord) -> str:
        row = _row_dict(rec, prefix="saikin-member", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_saikin_member", row)

    def put_vertex_ki_absorb(self, rec: KiAbsorbRecord) -> str:
        row = _row_dict(rec, prefix="ki-absorb", key_fields=("agent_did", "created_at"))
        return self._put("vertex_ki_absorb", row)

    def put_vertex_ki_artifact(self, rec: KiArtifactRecord) -> str:
        row = _row_dict(rec, prefix="ki-artifact", key_fields=("agent_did", "created_at"))
        return self._put("vertex_ki_artifact", row)

    def put_vertex_ki_ring(self, rec: KiRingRecord) -> str:
        row = _row_dict(rec, prefix="ki-ring", key_fields=("agent_did", "created_at"))
        return self._put("vertex_ki_ring", row)

    def put_edge_ki_vascular(self, rec: KiVascularRecord) -> str:
        row = _row_dict(rec, prefix="ki-vascular", key_fields=("src_vid", "dst_vid"))
        return self._put("edge_ki_vascular", row)

