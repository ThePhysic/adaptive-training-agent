-- Durable approved state only. Unapproved candidates and prompts never enter SQL.
CREATE TABLE approved_plans (
    plan_id text COLLATE "C" PRIMARY KEY CHECK (plan_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    owner_id text NOT NULL CHECK (owner_id IN ('synthetic-a', 'synthetic-b')),
    candidate_id text NOT NULL CHECK (candidate_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    candidate_revision integer NOT NULL CHECK (candidate_revision IN (1, 2)),
    content_hash text NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    profile_revision bigint NOT NULL CHECK (profile_revision > 0),
    catalog_revision text NOT NULL CHECK (catalog_revision ~ '^[A-Za-z0-9_-]{1,64}$'),
    validator_revision text NOT NULL CHECK (validator_revision ~ '^[A-Za-z0-9_-]{1,64}$'),
    plan_bytes bytea NOT NULL CHECK (octet_length(plan_bytes) BETWEEN 1 AND 65536),
    CHECK (encode(sha256(plan_bytes), 'hex') = content_hash),
    UNIQUE (owner_id, candidate_id),
    UNIQUE (owner_id, plan_id)
);

CREATE TABLE approval_idempotency (
    owner_id text NOT NULL,
    operation text NOT NULL CHECK (operation = 'approve_plan'),
    idempotency_key text NOT NULL CHECK (idempotency_key ~ '^[A-Za-z0-9_-]{1,128}$'),
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    plan_id text NOT NULL,
    PRIMARY KEY (owner_id, operation, idempotency_key),
    UNIQUE (owner_id, plan_id),
    FOREIGN KEY (owner_id, plan_id) REFERENCES approved_plans (owner_id, plan_id)
);

CREATE TABLE approval_audit (
    owner_id text NOT NULL,
    plan_id text NOT NULL,
    operation text NOT NULL CHECK (operation = 'approve_plan'),
    approved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    PRIMARY KEY (owner_id, plan_id),
    FOREIGN KEY (owner_id, plan_id) REFERENCES approved_plans (owner_id, plan_id)
);

-- Application-approved state is append-only, including its binding/audit.
-- Privileged DDL/migration access is outside this local synthetic boundary.
CREATE FUNCTION reject_approval_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Approved state is immutable' USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER approved_plans_immutable BEFORE UPDATE OR DELETE ON approved_plans
    FOR EACH ROW EXECUTE FUNCTION reject_approval_mutation();
CREATE TRIGGER approval_keys_immutable BEFORE UPDATE OR DELETE ON approval_idempotency
    FOR EACH ROW EXECUTE FUNCTION reject_approval_mutation();
CREATE TRIGGER approval_audit_immutable BEFORE UPDATE OR DELETE ON approval_audit
    FOR EACH ROW EXECUTE FUNCTION reject_approval_mutation();
CREATE TRIGGER approved_plans_no_truncate BEFORE TRUNCATE ON approved_plans
    FOR EACH STATEMENT EXECUTE FUNCTION reject_approval_mutation();
CREATE TRIGGER approval_keys_no_truncate BEFORE TRUNCATE ON approval_idempotency
    FOR EACH STATEMENT EXECUTE FUNCTION reject_approval_mutation();
CREATE TRIGGER approval_audit_no_truncate BEFORE TRUNCATE ON approval_audit
    FOR EACH STATEMENT EXECUTE FUNCTION reject_approval_mutation();
