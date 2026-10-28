-- Bounded numerical discrepancy evidence only; no live mode, permit or grant.
CREATE TABLE spend_observations (
    project_id text NOT NULL REFERENCES spend_projects,
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
