-- DriveVitals PostgreSQL initialization.
--
-- Runs once per fresh volume (the postgres image executes scripts in
-- /docker-entrypoint-initdb.d on first init only).
--
-- The development database itself is created by POSTGRES_DB. This script
-- additionally creates the dedicated database used by the backend test
-- suite: pytest fixtures drop and reseed every table in it on each run,
-- so it must never point at the development database.
CREATE DATABASE drivevitals_test;