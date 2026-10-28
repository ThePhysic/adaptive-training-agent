-- F3-04C separate probe accounting; no rows, active authority or monetary permit.
-- Derived structurally from 005-008; original migrations/replay constraints unchanged.

-- Empty offline-replay accounting infrastructure; creates no grant or live permit.
CREATE TABLE probe_spend_projects (
    project_id text PRIMARY KEY CHECK (project_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    limit_micro bigint NOT NULL CHECK (limit_micro BETWEEN 0 AND 1000000000),
    day_limit_micro bigint NOT NULL CHECK (day_limit_micro BETWEEN 0 AND 1000000000),
    disabled boolean NOT NULL DEFAULT false,
    frozen boolean NOT NULL DEFAULT false,
    mode text NOT NULL DEFAULT 'simulation' CHECK (mode IN ('simulation','live'))
);
CREATE TABLE probe_spend_grants (
    grant_id text PRIMARY KEY CHECK (grant_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    project_id text NOT NULL REFERENCES probe_spend_projects,
    limit_micro bigint NOT NULL CHECK (limit_micro BETWEEN 0 AND 1000000000),
    expires_at timestamptz NOT NULL,
    UNIQUE (grant_id, project_id)
);
CREATE TABLE probe_spend_sessions (
    session_id text PRIMARY KEY CHECK (session_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    grant_id text NOT NULL REFERENCES probe_spend_grants,
    limit_micro bigint NOT NULL CHECK (limit_micro BETWEEN 0 AND 1000000000),
    expires_at timestamptz NOT NULL,
    UNIQUE (session_id, grant_id)
);
CREATE TABLE probe_spend_attempts (
    attempt_id text PRIMARY KEY CHECK (attempt_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    project_id text NOT NULL REFERENCES probe_spend_projects,
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
    FOREIGN KEY (grant_id, project_id) REFERENCES probe_spend_grants(grant_id, project_id),
    FOREIGN KEY (session_id, grant_id) REFERENCES probe_spend_sessions(session_id, grant_id),
    UNIQUE (run_id, attempt_number),
    CHECK ((state = 'settled') = (actual_micro IS NOT NULL)),
    CHECK ((state = 'settled') = (usage IS NOT NULL)),
    CHECK ((state = 'settled') = (settlement_hash IS NOT NULL))
);
CREATE INDEX probe_spend_attempt_project ON probe_spend_attempts(project_id, day);

-- Ratified A-C, OFFLINE replay only. No grant, permit or live mode is inserted.
CREATE TABLE probe_spend_pairs (
    pair_id text PRIMARY KEY CHECK (pair_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    project_id text NOT NULL REFERENCES probe_spend_projects,
    grant_id text NOT NULL,
    session_id text NOT NULL,
    run_id text NOT NULL CHECK (run_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    ordinal integer NOT NULL CHECK (ordinal BETWEEN 1 AND 3),
    input_ceiling integer NOT NULL CHECK (input_ceiling BETWEEN 1 AND 16000),
    output_cap integer NOT NULL CHECK (output_cap BETWEEN 1 AND 2000),
    count_ceiling_micro bigint NOT NULL CHECK (count_ceiling_micro BETWEEN 1 AND 1000000000),
    count_quote text NOT NULL CHECK (count_quote = 'provider-count-bound-v1'),
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    FOREIGN KEY (grant_id,project_id) REFERENCES probe_spend_grants(grant_id,project_id),
    FOREIGN KEY (session_id,grant_id) REFERENCES probe_spend_sessions(session_id,grant_id),
    UNIQUE (run_id,ordinal),
    UNIQUE (pair_id,project_id,grant_id,session_id,run_id,ordinal)
);
CREATE TABLE probe_spend_operations (
    operation_id text PRIMARY KEY CHECK (operation_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    pair_id text NOT NULL,
    project_id text NOT NULL,
    grant_id text NOT NULL,
    session_id text NOT NULL,
    run_id text NOT NULL,
    ordinal integer NOT NULL,
    kind text NOT NULL CHECK (kind IN ('count','generation')),
    wire_ordinal integer CHECK (wire_ordinal BETWEEN 1 AND 6),
    day date NOT NULL,
    state text NOT NULL CHECK (state IN ('reserved','sent','responded_held','settled','not_sent')),
    reserved_micro bigint NOT NULL CHECK (reserved_micro >= 0),
    actual_micro bigint CHECK (actual_micro >= 0),
    input_bound integer NOT NULL CHECK (input_bound BETWEEN 0 AND 16000),
    output_cap integer NOT NULL CHECK (output_cap BETWEEN 0 AND 2000),
    counted_input integer CHECK (counted_input BETWEEN 1 AND 16000),
    usage jsonb,
    settlement_hash text CHECK (settlement_hash ~ '^[0-9a-f]{64}$'),
    FOREIGN KEY (pair_id,project_id,grant_id,session_id,run_id,ordinal)
      REFERENCES probe_spend_pairs(pair_id,project_id,grant_id,session_id,run_id,ordinal),
    UNIQUE (pair_id,kind),
    UNIQUE (run_id,kind,ordinal),
    UNIQUE (run_id,wire_ordinal),
    CHECK ((state='settled') = (actual_micro IS NOT NULL)),
    CHECK ((state='settled') = (settlement_hash IS NOT NULL)),
    CHECK ((state IN ('sent','responded_held','settled')) = (wire_ordinal IS NOT NULL)),
    CHECK (state <> 'responded_held' OR (kind='count' AND counted_input IS NOT NULL)),
    CHECK (kind <> 'count' OR (input_bound=0 AND output_cap=0 AND usage IS NULL)),
    CHECK (kind <> 'generation' OR (output_cap>0 AND counted_input IS NULL)),
    CHECK (kind <> 'generation' OR state <> 'settled' OR usage IS NOT NULL)
);
CREATE INDEX probe_spend_operations_project ON probe_spend_operations(project_id,day);

-- Additive quote provenance; never modify an applied migration/checksum.
ALTER TABLE probe_spend_pairs ADD COLUMN rate_version text NOT NULL
    DEFAULT 'sol-standard-2026-10-24-v1'
    CHECK (rate_version = 'sol-standard-2026-10-24-v1');

-- Bounded numerical discrepancy evidence only; no live mode, permit or grant.
CREATE TABLE probe_spend_observations (
    project_id text NOT NULL REFERENCES probe_spend_projects,
    source text NOT NULL CHECK (source IN ('legacy','mixed')),
    operation_id text NOT NULL CHECK (operation_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    reason text NOT NULL CHECK (reason IN
      ('model','tier','cache_ttl','usage_input','usage_output','cache_details',
       'usage_missing','usage_invalid','count_price')),
    model_class text NOT NULL CHECK (model_class IN ('expected','unexpected','missing')),
    tier_class text NOT NULL CHECK (tier_class IN ('expected','unexpected','missing')),
    numbers jsonb NOT NULL CHECK (
      jsonb_typeof(numbers)='object' AND octet_length(numbers::text)<=1024 AND
      numbers - ARRAY['input_tokens','output_tokens','cached_tokens','write_30m_tokens',
        'write_12h_tokens','reasoning_tokens','total_tokens','cache_write_tokens',
        'charge_micro']::text[] = '{}'::jsonb AND
      NOT jsonb_path_exists(numbers, '$.* ? (@.type() != "number")') AND
      NOT jsonb_path_exists(numbers, '$.* ? (@ < 0 || @ > 1000000000 || @.floor() != @)')),
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    observed_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id,source,operation_id)
);

-- Prepared proposals and nonmonetary fixtures are not active live authority.
CREATE TABLE probe_authorities (
    project_id text PRIMARY KEY REFERENCES probe_spend_projects,
    account_id text NOT NULL CHECK (account_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    authority_id text NOT NULL UNIQUE CHECK (authority_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    state text NOT NULL CHECK (state IN ('prepared','simulation','active','revoked')),
    specification jsonb NOT NULL CHECK (
        jsonb_typeof(specification)='object' AND octet_length(specification::text)<=8192 AND
        specification->>'project'=project_id AND specification->>'account'=account_id AND
        specification->>'model'='gpt-6.1-sol' AND specification->>'tier'='default' AND
        specification->>'rate_version'='sol-standard-2026-10-24-v1' AND
        specification->>'input_version'='compatibility-profile-v1'),
    fingerprint text NOT NULL CHECK (fingerprint ~ '^[0-9a-f]{64}$'),
    run_id text CHECK (run_id ~ '^[A-Za-z0-9_-]{1,64}$'),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (state <> 'active' OR
        (specification->'count_bound'->>'kind'='provider_reviewed' AND
         (specification->'count_bound'->>'ceiling_micro')::bigint > 0))
);
