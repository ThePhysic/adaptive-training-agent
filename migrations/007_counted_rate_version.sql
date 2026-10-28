-- Additive quote provenance; never modify an applied migration/checksum.
ALTER TABLE spend_pairs ADD COLUMN rate_version text NOT NULL
    DEFAULT 'sol-standard-2026-10-24-v1'
    CHECK (rate_version = 'sol-standard-2026-10-24-v1');
