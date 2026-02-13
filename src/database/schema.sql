-- Players table
CREATE TABLE IF NOT EXISTS players (
    player_id SERIAL PRIMARY KEY,
    fg_id VARCHAR(10) UNIQUE,
    bbref_id VARCHAR(20),
    name VARCHAR(100) NOT NULL,
    mlb_debut_date DATE,
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Season stats table
CREATE TABLE IF NOT EXISTS season_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    team VARCHAR(20),
    
    -- Counting stats
    games INTEGER,
    pa INTEGER,
    ab INTEGER,
    hits INTEGER,
    doubles INTEGER,
    triples INTEGER,
    hr INTEGER,
    rbi INTEGER,
    bb INTEGER,
    so INTEGER,
    
    -- Rate stats
    avg DECIMAL(5,3),
    obp DECIMAL(5,3),
    slg DECIMAL(5,3),
    woba DECIMAL(5,3),
    wrc_plus INTEGER,
    babip DECIMAL(5,3),
    
    -- Advanced stats
    bb_pct DECIMAL(5,1),
    k_pct DECIMAL(5,1),
    iso DECIMAL(5,3),
    
    -- Batted ball
    gb_pct DECIMAL(5,1),
    fb_pct DECIMAL(5,1),
    ld_pct DECIMAL(5,1),
    hr_fb_pct DECIMAL(5,1),
    
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season, team)
);

-- Statcast data
CREATE TABLE IF NOT EXISTS statcast_data (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    
    exit_velo DECIMAL(5,1),
    launch_angle DECIMAL(5,1),
    barrel_pct DECIMAL(5,1),
    hard_hit_pct DECIMAL(5,1),
    xba DECIMAL(5,3),
    xslg DECIMAL(5,3),
    xwoba DECIMAL(5,3),
    
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_season_stats_player ON season_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_season_stats_season ON season_stats(season);