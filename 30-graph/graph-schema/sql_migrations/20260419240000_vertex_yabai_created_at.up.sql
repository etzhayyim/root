ALTER TABLE vertex_yabai_risk ADD COLUMN IF NOT EXISTS created_at VARCHAR;

ALTER TABLE vertex_yabai_enforcement ADD COLUMN IF NOT EXISTS created_at VARCHAR;

ALTER TABLE vertex_yabai_registration_ban ADD COLUMN IF NOT EXISTS created_at VARCHAR;
