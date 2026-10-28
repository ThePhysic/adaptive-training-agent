-- Explicit synthetic session Submit only; never mutate an approved snapshot.
CREATE TABLE session_records (
    record_id text PRIMARY KEY CHECK (record_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    owner_id text NOT NULL CHECK (owner_id IN ('synthetic-a', 'synthetic-b')),
    plan_id text NOT NULL,
    day_index integer NOT NULL CHECK (day_index BETWEEN 1 AND 4),
    revision integer NOT NULL DEFAULT 1 CHECK (revision = 1),
    plan_revision integer NOT NULL CHECK (plan_revision IN (1,2)),
    plan_content_hash text NOT NULL CHECK (plan_content_hash ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('completed','partial','skipped')),
    effort text CHECK (effort IN ('easy','moderate','hard')),
    rating integer CHECK (rating BETWEEN 1 AND 5),
    submitted_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    CHECK (status <> 'skipped' OR (effort IS NULL AND rating IS NULL)),
    UNIQUE (owner_id, plan_id, day_index),
    UNIQUE (owner_id, record_id),
    FOREIGN KEY (owner_id, plan_id) REFERENCES approved_plans (owner_id, plan_id)
);

CREATE TABLE session_idempotency (
    owner_id text NOT NULL,
    operation text NOT NULL CHECK (operation = 'submit_session'),
    idempotency_key text NOT NULL CHECK (idempotency_key ~ '^[A-Za-z0-9_-]{1,128}$'),
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    record_id text NOT NULL,
    PRIMARY KEY (owner_id, operation, idempotency_key),
    UNIQUE (owner_id, record_id),
    FOREIGN KEY (owner_id, record_id) REFERENCES session_records (owner_id, record_id)
);

CREATE FUNCTION check_session_reference() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM approved_plans p
        WHERE p.owner_id=NEW.owner_id AND p.plan_id=NEW.plan_id
          AND p.candidate_revision=NEW.plan_revision AND p.content_hash=NEW.plan_content_hash
          AND EXISTS (
              SELECT 1 FROM jsonb_array_elements(convert_from(p.plan_bytes,'UTF8')::jsonb->'days') d
              WHERE (d->>'day_index')::integer=NEW.day_index
          )
    ) THEN
        RAISE EXCEPTION 'Invalid approved session reference' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER session_reference BEFORE INSERT ON session_records
    FOR EACH ROW EXECUTE FUNCTION check_session_reference();

CREATE FUNCTION check_session_binding() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM session_idempotency k
                   WHERE k.owner_id=NEW.owner_id AND k.record_id=NEW.record_id) THEN
        RAISE EXCEPTION 'Session requires its atomic key binding' USING ERRCODE='23514';
    END IF;
    RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER session_binding AFTER INSERT ON session_records
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION check_session_binding();

CREATE FUNCTION reject_session_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Submitted session state is immutable' USING ERRCODE='55000';
END;
$$;
CREATE TRIGGER session_records_immutable BEFORE UPDATE OR DELETE ON session_records
    FOR EACH ROW EXECUTE FUNCTION reject_session_mutation();
CREATE TRIGGER session_keys_immutable BEFORE UPDATE OR DELETE ON session_idempotency
    FOR EACH ROW EXECUTE FUNCTION reject_session_mutation();
CREATE TRIGGER session_records_no_truncate BEFORE TRUNCATE ON session_records
    FOR EACH STATEMENT EXECUTE FUNCTION reject_session_mutation();
CREATE TRIGGER session_keys_no_truncate BEFORE TRUNCATE ON session_idempotency
    FOR EACH STATEMENT EXECUTE FUNCTION reject_session_mutation();
