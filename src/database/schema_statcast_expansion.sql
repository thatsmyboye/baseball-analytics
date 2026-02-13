-- Statcast Data Table Expansion
-- Add new columns to existing statcast_data table

-- Add missing Statcast metrics
ALTER TABLE statcast_data
ADD COLUMN IF NOT EXISTS max_exit_velo DECIMAL(5,1),
ADD COLUMN IF NOT EXISTS ev_90th_percentile DECIMAL(5,1),
ADD COLUMN IF NOT EXISTS sweet_spot_pct DECIMAL(5,1),
ADD COLUMN IF NOT EXISTS batted_balls INTEGER,
ADD COLUMN IF NOT EXISTS gb_pct_statcast DECIMAL(5,1),
ADD COLUMN IF NOT EXISTS ld_pct_statcast DECIMAL(5,1),
ADD COLUMN IF NOT EXISTS fb_pct_statcast DECIMAL(5,1),
ADD COLUMN IF NOT EXISTS pu_pct_statcast DECIMAL(5,1);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_statcast_player_season ON statcast_data(player_id, season);
CREATE INDEX IF NOT EXISTS idx_statcast_season ON statcast_data(season);

-- Defensive stats table (for Baseball-Reference integration)
CREATE TABLE IF NOT EXISTS defensive_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    position VARCHAR(10),
    innings DECIMAL(6,1),
    games INTEGER,
    
    -- Defensive metrics
    drs INTEGER,                    -- Defensive Runs Saved
    uzr DECIMAL(5,1),              -- Ultimate Zone Rating
    outs_above_avg INTEGER,        -- Outs Above Average
    range_factor DECIMAL(5,2),     -- Range Factor
    
    -- Fielding percentages
    fielding_pct DECIMAL(5,3),
    putouts INTEGER,
    assists INTEGER,
    errors INTEGER,
    double_plays INTEGER,
    
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season, position)
);

-- Baserunning stats table
CREATE TABLE IF NOT EXISTS baserunning_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    
    -- Stolen bases
    sb INTEGER,
    cs INTEGER,
    sb_pct DECIMAL(5,1),
    
    -- Advanced baserunning
    bsr DECIMAL(5,1),              -- Baserunning Runs
    ubr DECIMAL(5,1),              -- Ultimate Base Running
    wgdp DECIMAL(5,1),             -- Weighted GDP Runs
    wsb DECIMAL(5,1),              -- Weighted Stolen Base Runs
    
    -- Extra bases taken
    extra_bases_taken INTEGER,
    times_out_on_bases INTEGER,
    
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season)
);

-- Situational splits table
CREATE TABLE IF NOT EXISTS situational_splits (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    split_type VARCHAR(20),        -- 'vs_lhp', 'vs_rhp', 'home', 'away', 'day', 'night'
    
    -- Basic counting stats
    pa INTEGER,
    ab INTEGER,
    hits INTEGER,
    hr INTEGER,
    bb INTEGER,
    so INTEGER,
    
    -- Rate stats
    avg DECIMAL(5,3),
    obp DECIMAL(5,3),
    slg DECIMAL(5,3),
    ops DECIMAL(5,3),
    woba DECIMAL(5,3),
    wrc_plus INTEGER,
    
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season, split_type)
);

-- Player metadata expansion
ALTER TABLE players
ADD COLUMN IF NOT EXISTS position VARCHAR(10),
ADD COLUMN IF NOT EXISTS bats VARCHAR(1),          -- L, R, S (switch)
ADD COLUMN IF NOT EXISTS throws VARCHAR(1),        -- L, R
ADD COLUMN IF NOT EXISTS height_inches INTEGER,
ADD COLUMN IF NOT EXISTS weight_lbs INTEGER,
ADD COLUMN IF NOT EXISTS mlbam_id VARCHAR(10);

-- Add index on MLB AM ID for Statcast lookups
CREATE INDEX IF NOT EXISTS idx_players_mlbam ON players(mlbam_id);

-- Indexes for new tables
CREATE INDEX IF NOT EXISTS idx_defensive_player_season ON defensive_stats(player_id, season);
CREATE INDEX IF NOT EXISTS idx_baserunning_player_season ON baserunning_stats(player_id, season);
CREATE INDEX IF NOT EXISTS idx_splits_player_season ON situational_splits(player_id, season);

-- Comments
COMMENT ON TABLE statcast_data IS 'Statcast metrics from Baseball Savant (2015+)';
COMMENT ON TABLE defensive_stats IS 'Defensive metrics from Baseball-Reference';
COMMENT ON TABLE baserunning_stats IS 'Baserunning value metrics';
COMMENT ON TABLE situational_splits IS 'Performance splits by situation';

COMMENT ON COLUMN statcast_data.exit_velo IS 'Average exit velocity (mph)';
COMMENT ON COLUMN statcast_data.launch_angle IS 'Average launch angle (degrees)';
COMMENT ON COLUMN statcast_data.barrel_pct IS 'Barrel rate (%)';
COMMENT ON COLUMN statcast_data.hard_hit_pct IS 'Hard-hit rate - 95+ mph (%)';
COMMENT ON COLUMN statcast_data.sweet_spot_pct IS 'Sweet spot rate - 8-32 degrees (%)';
COMMENT ON COLUMN statcast_data.xba IS 'Expected batting average';
COMMENT ON COLUMN statcast_data.xslg IS 'Expected slugging percentage';
COMMENT ON COLUMN statcast_data.xwoba IS 'Expected weighted on-base average';
