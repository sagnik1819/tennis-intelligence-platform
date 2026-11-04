-- ==============================================================================
-- TENNIS INTELLIGENCE PLATFORM (TIP) - POSTGRESQL DDL SCHEMA
-- Normalized 3NF Schema with Foreign Keys, Constraints, and Optimized Indexes
-- ==============================================================================

-- Drop tables if re-initializing (in reverse foreign-key order)
DROP TABLE IF EXISTS ai_interactions CASCADE;
DROP TABLE IF EXISTS user_favourites CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS sync_logs CASCADE;
DROP TABLE IF EXISTS competitor_rankings CASCADE;
DROP TABLE IF EXISTS competitors CASCADE;
DROP TABLE IF EXISTS venues CASCADE;
DROP TABLE IF EXISTS complexes CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- 1. CATEGORIES TABLE
CREATE TABLE categories (
    category_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

-- 2. COMPETITIONS TABLE
CREATE TABLE competitions (
    competition_id VARCHAR(50) PRIMARY KEY,
    competition_name VARCHAR(100) NOT NULL,
    parent_id VARCHAR(50) NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'doubles',
    gender VARCHAR(10) NOT NULL DEFAULT 'men',
    category_id VARCHAR(50) NOT NULL,
    CONSTRAINT fk_comp_category FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
    CONSTRAINT fk_comp_parent FOREIGN KEY (parent_id) REFERENCES competitions(competition_id) ON DELETE SET NULL
);

-- 3. COMPLEXES TABLE
CREATE TABLE complexes (
    complex_id VARCHAR(50) PRIMARY KEY,
    complex_name VARCHAR(100) NOT NULL
);

-- 4. VENUES TABLE
CREATE TABLE venues (
    venue_id VARCHAR(50) PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    timezone VARCHAR(100) NOT NULL DEFAULT 'UTC',
    complex_id VARCHAR(50) NOT NULL,
    CONSTRAINT fk_venue_complex FOREIGN KEY (complex_id) REFERENCES complexes(complex_id) ON DELETE CASCADE
);

-- 5. COMPETITORS TABLE
CREATE TABLE competitors (
    competitor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL
);

-- 6. COMPETITOR_RANKINGS TABLE
CREATE TABLE competitor_rankings (
    rank_id SERIAL PRIMARY KEY,
    rank INT NOT NULL CHECK (rank >= 1),
    movement INT NOT NULL DEFAULT 0,
    points INT NOT NULL CHECK (points >= 0),
    competitions_played INT NOT NULL CHECK (competitions_played >= 0),
    competitor_id VARCHAR(50) NOT NULL,
    CONSTRAINT fk_ranking_competitor FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id) ON DELETE CASCADE
);

-- 7. USERS TABLE (Authentication & Roles)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. USER_FAVOURITES TABLE (Personalized Workspace)
CREATE TABLE user_favourites (
    fav_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    competitor_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fav_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_fav_competitor FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id) ON DELETE CASCADE,
    CONSTRAINT uq_user_competitor UNIQUE (user_id, competitor_id)
);

-- 9. AI_INTERACTIONS TABLE (Chat History & Grounded RAG)
CREATE TABLE ai_interactions (
    interaction_id SERIAL PRIMARY KEY,
    user_id INT NULL,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ai_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 10. SYNC_LOGS TABLE (Data Quality & Freshness)
CREATE TABLE sync_logs (
    sync_id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    data_mode VARCHAR(50) NOT NULL,
    records_processed INT NOT NULL DEFAULT 0,
    duration_seconds NUMERIC(6, 2) DEFAULT 0.0,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- ==============================================================================
CREATE INDEX idx_competitions_category ON competitions(category_id);
CREATE INDEX idx_competitions_parent ON competitions(parent_id);
CREATE INDEX idx_venues_complex ON venues(complex_id);
CREATE INDEX idx_venues_country ON venues(country_name);
CREATE INDEX idx_competitors_country ON competitors(country);
CREATE INDEX idx_rankings_rank ON competitor_rankings(rank);
CREATE INDEX idx_rankings_points ON competitor_rankings(points DESC);
CREATE INDEX idx_rankings_competitor ON competitor_rankings(competitor_id);
CREATE INDEX idx_user_favourites_user ON user_favourites(user_id);
