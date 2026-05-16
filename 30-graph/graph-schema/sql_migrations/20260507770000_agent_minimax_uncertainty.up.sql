ALTER TABLE vertex_agent_minimax_evaluation
    ADD COLUMN IF NOT EXISTS counterparty_uncertainty DOUBLE PRECISION NOT NULL DEFAULT 0.0;
