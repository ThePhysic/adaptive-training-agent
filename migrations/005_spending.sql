-- Empty offline-replay accounting infrastructure; creates no grant or live permit.
CREATE TABLE spend_projects (
    project_id text PRIMARY KEY CHECK (project_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    limit_micro bigint NOT NULL CHECK (limit_micro BETWEEN 0 AND 1000000000),
    day_limit_micro bigint NOT NULL CHECK (day_limit_micro BETWEEN 0 AND 1000000000),
    disabled boolean NOT NULL DEFAULT false,
    frozen boolean NOT NULL DEFAULT false,
    mode text NOT NULL DEFAULT 'replay' CHECK (mode = 'replay')
);
CREATE TABLE spend_grants (
    grant_id text PRIMARY KEY CHECK (grant_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    project_id text NOT NULL REFERENCES spend_projects,
    limit_micro bigint NOT NULL CHECK (limit_micro BETWEEN 0 AND 1000000000),
    expires_at timestamptz NOT NULL,
    UNIQUE (grant_id, project_id)
);
CREATE TABLE spend_sessions (
    session_id text PRIMARY KEY CHECK (session_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    grant_id text NOT NULL REFERENCES spend_grants,
    limit_micro bigint NOT NULL CHECK (limit_micro BETWEEN 0 AND 1000000000),
    expires_at timestamptz NOT NULL,
    UNIQUE (session_id, grant_id)
);
CREATE TABLE spend_attempts (
    attempt_id text PRIMARY KEY CHECK (attempt_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    project_id text NOT NULL REFERENCES spend_projects,
    grant_id text NOT NULL,
    session_id text NOT NULL,
    run_id text NOT NULL CHECK (run_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    attempt_number integer NOT NULL CHECK (attempt_number BETWEEN 1 AND 3),
    day date NOT NULL,
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    input_bound integer NOT NULL CHECK (input_bound BETWEEN 0 AND 16000),
    output_cap integer NOT NULL CHECK (output_cap BETWEEN 1 AND 2000),
    reserved_micro bigint NOT NULL CHECK (reserved_micro BETWEEN 0 AND 80000),
    state text NOT NULL CHECK (state IN ('reserved','sent','settled','not_sent')),
    actual_micro bigint CHECK (actual_micro >= 0),
    usage jsonb,
    settlement_hash text CHECK (settlement_hash ~ '^[0-9a-f]{64}$'),
    rate_version text NOT NULL CHECK (rate_version = 'sol-standard-2026-10-24-v1'),
    FOREIGN KEY (grant_id, project_id) REFERENCES spend_grants(grant_id, project_id),
    FOREIGN KEY (session_id, grant_id) REFERENCES spend_sessions(session_id, grant_id),
    UNIQUE (run_id, attempt_number),
    CHECK ((state = 'settled') = (actual_micro IS NOT NULL)),
    CHECK ((state = 'settled') = (usage IS NOT NULL)),
    CHECK ((state = 'settled') = (settlement_hash IS NOT NULL))
);
CREATE INDEX spend_attempt_project ON spend_attempts(project_id, day);
