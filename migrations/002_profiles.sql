-- Explicit Save only. No candidate, approved-plan, approval or idempotency tables.
CREATE TABLE profiles (
    owner_id text PRIMARY KEY CHECK (owner_id IN ('synthetic-a', 'synthetic-b')),
    revision bigint NOT NULL CHECK (revision > 0),
    preferences jsonb NOT NULL CHECK (jsonb_typeof(preferences) = 'object')
);
