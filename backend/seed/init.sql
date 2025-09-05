CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  external_id VARCHAR(64) UNIQUE,
  name TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
  id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(id),
  iban VARCHAR(34) UNIQUE,
  opened_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMP NOT NULL,
  src_account_id INT REFERENCES accounts(id),
  dst_account_id INT,
  dst_iban VARCHAR(34),
  amount_cents BIGINT NOT NULL,
  currency CHAR(3) NOT NULL,
  channel VARCHAR(16) NOT NULL,
  is_first_to_payee BOOLEAN DEFAULT FALSE,
  device_fp VARCHAR(128),
  risk_score REAL DEFAULT 0,
  risk_reasons JSONB DEFAULT '[]'::jsonb,
  action VARCHAR(16) DEFAULT 'allow'
);

CREATE TABLE IF NOT EXISTS watchlist (
  id SERIAL PRIMARY KEY,
  iban VARCHAR(34) UNIQUE,
  label TEXT,
  risk_level INT DEFAULT 80
);

CREATE INDEX IF NOT EXISTS idx_txn_ts ON transactions(ts);
CREATE INDEX IF NOT EXISTS idx_txn_src ON transactions(src_account_id);
CREATE INDEX IF NOT EXISTS idx_txn_dstiban ON transactions(dst_iban);
