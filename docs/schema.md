# Database Schema for the events table

```sql
-- Table: events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,  -- Auto-incrementing integer
    name VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- e.g., "AERC", "SERA", "OtherSource"
    event_type VARCHAR(50) NOT NULL, -- "endurance", "competitive_trail", etc.
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    location_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    region VARCHAR(50),
    is_canceled BOOLEAN DEFAULT FALSE,
    is_multi_day_event BOOLEAN DEFAULT FALSE,
    is_pioneer_ride BOOLEAN DEFAULT FALSE,
    ride_days INTEGER,
    ride_manager VARCHAR(255),
    manager_email VARCHAR(255),
    manager_phone VARCHAR(50),
    website VARCHAR(255),
    flyer_url VARCHAR(255),
    has_intro_ride BOOLEAN DEFAULT FALSE,
    ride_id VARCHAR(50),  -- Keep this as VARCHAR, as IDs may not always be numeric.
    latitude DOUBLE PRECISION,  -- Use DOUBLE PRECISION for lat/long
    longitude DOUBLE PRECISION,
    geocoding_attempted BOOLEAN DEFAULT FALSE, -- Track geocoding attempts
    description TEXT,
    control_judges JSONB, -- Use JSONB for efficient querying of judge data
    distances JSONB,      -- Store distances as a JSONB array
    directions TEXT,
     UNIQUE (source, ride_id)  -- Ensure uniqueness per source and ride_id
);
```
