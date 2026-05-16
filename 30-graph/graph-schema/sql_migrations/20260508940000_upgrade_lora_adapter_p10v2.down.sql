ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS display_name_yomi;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS adapter_format;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS adapter_alpha;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS adapter_rank;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS base_model;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS weight_sha256;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS weight_byte_size;

ALTER TABLE vertex_lora_adapter DROP COLUMN IF EXISTS weight_b2_uri;
