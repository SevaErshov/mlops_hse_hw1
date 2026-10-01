CREATE TABLE IF NOT EXISTS transaction_scores (
    id BIGSERIAL PRIMARY KEY,
    transaction_id TEXT UNIQUE NOT NULL,
    score DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 1),
    fraud_flag SMALLINT NOT NULL CHECK (fraud_flag IN (0, 1)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS fraud_latest_idx
ON transaction_scores (id DESC) WHERE fraud_flag = 1;
