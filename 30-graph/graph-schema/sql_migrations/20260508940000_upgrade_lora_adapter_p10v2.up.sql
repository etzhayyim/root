ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS weight_b2_uri     VARCHAR;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS weight_byte_size  BIGINT;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS weight_sha256     VARCHAR;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS base_model        VARCHAR;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS adapter_rank      INTEGER;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS adapter_alpha     DOUBLE PRECISION;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS adapter_format    VARCHAR;

ALTER TABLE vertex_lora_adapter ADD COLUMN IF NOT EXISTS display_name_yomi VARCHAR;

CREATE INDEX IF NOT EXISTS idx_lora_adapter_owner_did    ON vertex_lora_adapter (owner_did);

CREATE INDEX IF NOT EXISTS idx_lora_adapter_base_model   ON vertex_lora_adapter (base_model);

CREATE INDEX IF NOT EXISTS idx_lora_adapter_weight_b2    ON vertex_lora_adapter (weight_b2_uri);
