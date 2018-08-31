
CREATE MATERIALIZED VIEW IF NOT EXISTS processed.classifications AS (
   SELECT classification FROM records
      GROUP BY classification) WITH data;

CREATE MATERIALIZED VIEW IF NOT EXISTS processed.builds AS (
   SELECT count(build), build FROM records
      WHERE build::Numeric > 10000 AND build::Numeric < 100000
      GROUP BY build ORDER BY build::Numeric) WITH data;

CREATE MATERIALIZED VIEW IF NOT EXISTS processed.os_map AS (
   SELECT system_name, build FROM records
      WHERE build::Numeric > 10000 AND build::Numeric < 100000
      GROUP BY system_name, build) WITH data;
