-- Database setup for Cloud SQL PostgreSQL instance
-- Run these commands to set up the carpool database

-- Create database (if not exists)
CREATE DATABASE carpool_db;

-- Create user (if not exists)
CREATE USER carpool WITH PASSWORD 'Carpool@80';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE carpool_db TO carpool;

-- Connect to carpool_db and grant schema privileges
\c carpool_db;
GRANT ALL ON SCHEMA public TO carpool;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO carpool;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO carpool;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO carpool;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO carpool;
