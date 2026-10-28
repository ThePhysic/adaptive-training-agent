-- F1-01 bootstrap only. Profile/candidate/approval persistence belongs to F1-03/F1-06.
CREATE TABLE foundation_metadata (
    key text PRIMARY KEY,
    value text NOT NULL
);
INSERT INTO foundation_metadata (key, value) VALUES ('stage', 'F1-01');
