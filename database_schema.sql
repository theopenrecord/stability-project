-- Northwoods Housing Security Resource Database Schema
-- PostgreSQL with PostGIS extension for geospatial queries

-- Enable PostGIS extension for location-based queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- Resource Types Enum
CREATE TYPE resource_category AS ENUM (
    'food',
    'shelter',
    'healthcare',
    'waste_disposal',
    'propane',
    'camping',
    'day_center',
    'hygiene',
    'mail_address',
    'wifi_charging',
    'case_management',
    'transportation',
    'assistance_program',
    'land_opportunity',
    'legal_aid',
    'employment',
    'education',
    'veterans',
    'other'
);

-- Access Tier Enum
CREATE TYPE access_tier AS ENUM (
    'public',              -- Anyone can see
    'verified_user',       -- Requires email verification + geographic confirmation
    'trusted_verifier',    -- Case workers, social workers, community partners
    'admin'
);

-- Verification Method Enum
CREATE TYPE verification_method AS ENUM (
    'manual_physical',     -- Someone went there
    'manual_phone',        -- Called to verify
    'automated_web',       -- Bot checked website
    'community_report',    -- User reported current status
    'partner_verified'     -- Official partner organization verified
);

-- Report Type Enum
CREATE TYPE report_type AS ENUM (
    'still_open',
    'closed',
    'changed_hours',
    'changed_services',
    'not_helpful',
    'safety_concern',
    'new_restrictions',
    'other'
);

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash VARCHAR(255), -- For future authentication
    access_level access_tier DEFAULT 'public',
    county VARCHAR(100),  -- Geographic context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_access_level ON users(access_level);

-- Resources Table
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    resource_type resource_category NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    address TEXT,
    location GEOGRAPHY(POINT, 4326),  -- PostGIS point for lat/long
    county VARCHAR(100) NOT NULL,
    town VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(500),
    
    -- Hours and availability
    hours_of_operation TEXT,  -- Could be JSON but keeping simple for MVP
    seasonal_availability_summer BOOLEAN DEFAULT TRUE,
    seasonal_availability_winter BOOLEAN DEFAULT TRUE,
    
    -- Access and restrictions
    restrictions TEXT,  -- "Must have ID", "No pets", etc.
    access_tier access_tier DEFAULT 'public',
    
    -- Verification tracking
    last_verified_date TIMESTAMP,
    verification_source VARCHAR(255),
    verification_confidence INTEGER DEFAULT 50,  -- 0-100 scale
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Additional structured data
    capacity INTEGER,  -- For shelters, meal programs
    cost_info TEXT,  -- "$5", "Free", "Sliding scale"
    languages_supported TEXT[],  -- Array of language codes
    
    -- Special fields for specific resource types
    dump_station_fee DECIMAL(10,2),  -- For waste disposal sites
    propane_price_per_gallon DECIMAL(10,2),  -- For propane refill locations
    camping_nightly_rate DECIMAL(10,2)  -- For campgrounds
);

-- Indexes for performance
CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_resources_county ON resources(county);
CREATE INDEX idx_resources_access_tier ON resources(access_tier);
CREATE INDEX idx_resources_active ON resources(is_active);
CREATE INDEX idx_resources_location ON resources USING GIST(location);  -- Spatial index
CREATE INDEX idx_resources_verified ON resources(last_verified_date);

-- Verification Logs Table
CREATE TABLE verification_logs (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    verified_by INTEGER REFERENCES users(id),
    verification_method verification_method NOT NULL,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    confidence_score INTEGER,  -- 0-100
    previous_data JSONB  -- Store what changed if anything
);

CREATE INDEX idx_verification_resource ON verification_logs(resource_id);
CREATE INDEX idx_verification_date ON verification_logs(verified_at);

-- Community Reports Table
CREATE TABLE community_reports (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    reported_by INTEGER REFERENCES users(id),
    report_type report_type NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, reviewed, resolved, dismissed
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    admin_notes TEXT
);

CREATE INDEX idx_reports_resource ON community_reports(resource_id);
CREATE INDEX idx_reports_status ON community_reports(status);
CREATE INDEX idx_reports_created ON community_reports(created_at);

-- Assessment Results Table (anonymous data collection for advocacy)
CREATE TABLE assessment_results (
    id SERIAL PRIMARY KEY,
    risk_score INTEGER NOT NULL,  -- Calculated score
    risk_tier VARCHAR(20) NOT NULL,  -- green, yellow, orange, red
    county VARCHAR(100),
    age_range VARCHAR(20),  -- Optional anonymous demographic
    household_size INTEGER,  -- Optional
    housing_situation VARCHAR(100),  -- Optional: "renting", "owned", "vehicle", "tent", etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255)  -- To potentially follow up without identifying user
);

CREATE INDEX idx_assessment_county ON assessment_results(county);
CREATE INDEX idx_assessment_tier ON assessment_results(risk_tier);
CREATE INDEX idx_assessment_created ON assessment_results(created_at);

-- Memory Controls / User Edits Table
CREATE TABLE memory_controls (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    control_text TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memory_user ON memory_controls(user_id);

-- Resource Tags (for flexible categorization)
CREATE TABLE resource_tags (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_resource ON resource_tags(resource_id);
CREATE INDEX idx_tags_tag ON resource_tags(tag);

-- Saved Resources (users can bookmark)
CREATE TABLE saved_resources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    notes TEXT,  -- User's personal notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, resource_id)
);

CREATE INDEX idx_saved_user ON saved_resources(user_id);

-- Update trigger for resources updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries

-- Stale resources (need verification)
CREATE VIEW stale_resources AS
SELECT 
    r.*,
    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - r.last_verified_date)) as days_since_verified
FROM resources r
WHERE r.is_active = TRUE
  AND (r.last_verified_date IS NULL 
       OR r.last_verified_date < CURRENT_TIMESTAMP - INTERVAL '90 days')
ORDER BY r.last_verified_date ASC NULLS FIRST;

-- Resources with recent issues (community reports)
CREATE VIEW resources_with_concerns AS
SELECT 
    r.*,
    COUNT(cr.id) as concern_count,
    MAX(cr.created_at) as latest_concern
FROM resources r
JOIN community_reports cr ON r.id = cr.resource_id
WHERE cr.status = 'pending'
  AND cr.report_type IN ('closed', 'safety_concern', 'not_helpful')
  AND cr.created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY r.id
HAVING COUNT(cr.id) >= 2
ORDER BY concern_count DESC;

-- Highly verified resources (multiple recent verifications)
CREATE VIEW trusted_resources AS
SELECT 
    r.*,
    COUNT(vl.id) as verification_count,
    MAX(vl.verified_at) as latest_verification,
    AVG(vl.confidence_score) as avg_confidence
FROM resources r
JOIN verification_logs vl ON r.id = vl.resource_id
WHERE vl.verified_at > CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY r.id
HAVING COUNT(vl.id) >= 2
  AND AVG(vl.confidence_score) >= 70
ORDER BY verification_count DESC, latest_verification DESC;

-- Sample data insert function for testing
CREATE OR REPLACE FUNCTION insert_sample_data()
RETURNS void AS $$
BEGIN
    -- Insert a test resource
    INSERT INTO resources (
        resource_type,
        name,
        description,
        address,
        location,
        county,
        town,
        phone,
        website,
        hours_of_operation,
        seasonal_availability_winter,
        restrictions,
        access_tier,
        last_verified_date
    ) VALUES (
        'food',
        'Atlanta Community Food Pantry',
        'Food pantry serving Montmorency County residents. Provides emergency food boxes.',
        '123 Main St, Atlanta, MI 49709',
        ST_GeogFromText('POINT(-84.1434 45.0042)'),  -- Atlanta, MI coordinates
        'Montmorency',
        'Atlanta',
        '(989) 555-0100',
        'http://example.com/foodpantry',
        'Wednesdays 2-5pm, Saturdays 10am-1pm',
        true,
        'Proof of residency required, limited to once per week',
        'public',
        CURRENT_TIMESTAMP
    );
    
    INSERT INTO resources (
        resource_type,
        name,
        description,
        location,
        county,
        town,
        cost_info,
        dump_station_fee,
        access_tier,
        seasonal_availability_winter
    ) VALUES (
        'waste_disposal',
        'Atlanta RV Dump Station',
        'RV waste disposal station available year-round',
        ST_GeogFromText('POINT(-84.1400 45.0050)'),
        'Montmorency',
        'Atlanta',
        'Free for residents, $10 for non-residents',
        10.00,
        'public',
        true
    );
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE resources IS 'Core table containing all housing security resources across the Northwoods region';
COMMENT ON TABLE verification_logs IS 'Tracks verification history for data freshness and accuracy';
COMMENT ON TABLE community_reports IS 'User-submitted reports about resource status changes or issues';
COMMENT ON TABLE assessment_results IS 'Anonymous housing security self-assessment data for advocacy';
COMMENT ON COLUMN resources.location IS 'PostGIS geography point for proximity searches';
COMMENT ON COLUMN resources.verification_confidence IS 'Confidence score 0-100 based on verification recency and method';
