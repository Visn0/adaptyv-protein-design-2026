-- One row per page view, for the /stats page and /stats.json (site/PLAN.md).
-- The Worker writes one row per counted page view. The visitor value is a
-- truncated salted hash; no raw addresses are stored.
CREATE TABLE IF NOT EXISTS hits (
  day     TEXT NOT NULL,           -- YYYY-MM-DD, UTC
  path    TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'XX',
  visitor TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hits_day ON hits (day);
