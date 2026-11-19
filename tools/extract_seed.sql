-- Writes sim/seed/ds01_sample.csv: the DS01 rows the simulated data sets are built from.
-- One hour of the subset in docs/design.md (Uber trips picked up in Manhattan, March 2024), three pickup zones.
-- Reads the whole month once (508 MB over HTTPS). Run from the repository root:
--   uvx --from duckdb-cli duckdb < tools/extract_seed.sql
COPY (
  SELECT request_datetime, pickup_datetime, dropoff_datetime,
         PULocationID AS pickup_zone_id, DOLocationID AS dropoff_zone_id,
         trip_miles, trip_time AS trip_time_s, base_passenger_fare AS fare, driver_pay
  FROM 'https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2024-03.parquet'
  WHERE hvfhs_license_num = 'HV0003'                     -- Uber
    AND PULocationID IN (48, 161, 230)                   -- Clinton East, Midtown Center, Times Sq/Theatre District
    AND request_datetime >= TIMESTAMP '2024-03-14 08:00:00'   -- New York local time, as in the source
    AND request_datetime <  TIMESTAMP '2024-03-14 09:00:00'
  ORDER BY request_datetime, pickup_zone_id, dropoff_datetime, trip_miles
) TO 'sim/seed/ds01_sample.csv' (HEADER);
