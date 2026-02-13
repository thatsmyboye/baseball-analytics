# Implementation Guide

Complete step-by-step guide to implement the baseball analytics expansion.

---

## Prerequisites

### System Requirements
- Python 3.12+
- PostgreSQL database (Railway or local)
- ~10 GB free disk space
- Internet connection for API calls

### Installed Dependencies
```bash
pip install -r requirements.txt
```

---

## Phase 1: Player Database Expansion

### Goal
Expand from 53 to 400-600 active MLB players.

### Timeline
3-5 hours (including API rate limiting)

### Steps

#### Step 1.1: Run Player Discovery (5 minutes)
```bash
python src/scripts/discover_all_active_players.py
```

**What it does:**
- Fetches all qualified batters from 2023-2025 seasons
- Looks up FanGraphs IDs via pybaseball
- Exports list of new players

**Expected output:**
- `discovered_active_players.txt` - Human-readable list
- `new_verified_players.py` - Python format for loading

**Configuration options:**
- Seasons: Default [2023, 2024, 2025]
- Minimum PA: Default 50

#### Step 1.2: Review Discovered Players (2 minutes)
Open `discovered_active_players.txt` and review:
- Player names look correct
- FanGraphs IDs are present
- Remove any duplicates or unwanted players

#### Step 1.3: Batch Load Players (2-4 hours)
```bash
python src/scripts/load_discovered_players.py
```

**What it does:**
- Loads each player's 2015-2025 FanGraphs stats
- Progress tracking with resume capability
- Rate limiting (2 seconds between requests)

**Expected results:**
- 400-600 new players added
- 90%+ success rate
- Total database: 450-650 players

**If interrupted:**
- Script saves progress to `player_loading_progress.json`
- Resume by running the script again

**Troubleshooting:**
- **High failure rate:** Check internet connection, try increasing rate limit
- **API errors:** Wait 10 minutes and resume
- **Database errors:** Check PostgreSQL connection

---

## Phase 2A: Statcast Integration

### Goal
Add Statcast metrics for all players (2020-2025).

### Timeline
2-4 hours (depending on player count)

### Steps

#### Step 2A.1: Update Database Schema (1 minute)
```bash
# Connect to your PostgreSQL database
psql $DATABASE_URL

# Or use your preferred database tool (DBeaver, pgAdmin, etc.)
# Then run:
\i src/database/schema_statcast_expansion.sql
```

**What it does:**
- Adds new columns to `statcast_data` table
- Creates `defensive_stats`, `baserunning_stats`, `situational_splits` tables
- Adds indexes for performance

**Verify:**
```sql
\d statcast_data
-- Should show new columns: max_exit_velo, ev_90th_percentile, sweet_spot_pct, etc.
```

#### Step 2A.2: Fetch Statcast Data (2-4 hours)
```bash
python src/scrapers/statcast_scraper.py
```

**What it does:**
- Maps FanGraphs IDs to MLB AM IDs (required for Statcast)
- Fetches raw Statcast data from Baseball Savant
- Aggregates to season-level metrics
- Inserts into database

**Expected results:**
- 300-500 players with Statcast data (not all players have it)
- 2020-2025 seasons covered
- Metrics: exit velo, hard-hit%, barrel%, xwOBA, etc.

**Configuration options:**
- Seasons: Default [2020, 2021, 2022, 2023, 2024, 2025]
- Can adjust to [2015-2025] for full history (longer runtime)

**Troubleshooting:**
- **Many players with no data:** Normal - not all players have sufficient batted balls
- **Slow progress:** Statcast API is slower than FanGraphs, be patient
- **Connection timeouts:** Increase `time.sleep()` delay in code

#### Step 2A.3: Test Enhanced Regression Detection (1 minute)
```bash
python src/analytics/statcast_regression_detector.py
```

**What it does:**
- Runs regression detection with Statcast enhancements
- Shows BUY/SELL signals using both traditional + Statcast metrics

**Expected output:**
- Players with "STATCAST_UNLUCKY" or "STATCAST_LUCKY" signals
- "UNSUSTAINABLE_POWER" or "UNLUCKY_POWER" signals
- "EV_DECLINE" signals

**Example:**
```
🟢 STRONG BUY CANDIDATES

Anthony Santander (Orioles) - Net: +2.0
  🟢 TIER 1 STATCAST_UNLUCKY: BABIP 0.218 is low but hard-hit% 47.2% is up +3.5% - Unlucky!
  🟢 TIER 1 UNLUCKY_POWER: ISO down -0.062 but EV up +1.3 mph, Barrel% up +2.1% - Unlucky power!
```

---

## Phase 2B: Baseball-Reference Integration (Optional)

### Goal
Add defensive metrics, baserunning stats, and situational splits.

### Timeline
1-2 days (requires additional scraper development)

### Status
**Database schema created**, but scrapers not yet implemented.

### Next Steps (if desired)
1. Create `src/scrapers/baseball_reference.py`
2. Use existing `beautifulsoup4` to scrape B-Ref pages
3. Populate new tables: `defensive_stats`, `baserunning_stats`, `situational_splits`

**Note:** This is lower priority - focus on Phases 1 and 2A first.

---

## Phase 3: Dashboard Development

### Goal
Create interactive Streamlit dashboard for data visualization.

### Timeline
10-30 minutes (setup and testing)

### Steps

#### Step 3.1: Install Dashboard Dependencies (1 minute)
```bash
pip install streamlit plotly
```

#### Step 3.2: Launch Dashboard (1 minute)
```bash
streamlit run dashboard/app.py
```

**What happens:**
- Streamlit server starts on `http://localhost:8501`
- Browser opens automatically
- Dashboard loads data from database

#### Step 3.3: Explore Features (5-10 minutes)
Test each page:

1. **Home** - Overview and stats summary
2. **Player Search** - Look up players, view stats/charts
3. **Regression Signals** - Browse BUY/SELL candidates
4. **Predictions** - View 2026 projections
5. **League Stats** - Leaderboards and comparisons

#### Step 3.4: Customize (Optional)
Edit `dashboard/app.py` to:
- Change colors/theme
- Add new charts
- Modify layouts
- Add custom metrics

**Theme customization:**
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

---

## Verification & Testing

### Phase 1 Verification
```sql
-- Check player count
SELECT COUNT(*) FROM players;
-- Expected: 450-650

-- Check season coverage
SELECT player_id, COUNT(*) as seasons
FROM season_stats
GROUP BY player_id
ORDER BY seasons DESC
LIMIT 10;
-- Expected: 10-11 seasons per player

-- Check recent data
SELECT COUNT(DISTINCT player_id)
FROM season_stats
WHERE season = 2025;
-- Expected: 400-500 players
```

### Phase 2A Verification
```sql
-- Check Statcast coverage
SELECT COUNT(DISTINCT player_id) FROM statcast_data;
-- Expected: 300-500 players

-- Check Statcast metrics
SELECT season, COUNT(*) as players, AVG(exit_velo) as avg_ev
FROM statcast_data
GROUP BY season
ORDER BY season;
-- Expected: Increasing coverage, EV ~88-90 mph

-- Sample Statcast data
SELECT p.name, s.season, s.exit_velo, s.hard_hit_pct, s.barrel_pct
FROM statcast_data s
JOIN players p ON s.player_id = p.player_id
WHERE s.season = 2025
LIMIT 10;
```

### Dashboard Verification
1. Player search works
2. Charts render correctly
3. Data loads within 3 seconds
4. No console errors

---

## Common Issues & Solutions

### Issue 1: Player Discovery Finds Too Few Players
**Cause:** Seasons or PA threshold too restrictive
**Solution:** 
```python
# In discover_all_active_players.py
seasons = [2022, 2023, 2024, 2025]  # Add 2022
min_pa = 25  # Lower threshold
```

### Issue 2: Batch Loading Has High Failure Rate
**Cause:** API rate limiting or connection issues
**Solution:**
```python
# In load_discovered_players.py
rate_limit_seconds = 3  # Increase from 2 to 3
```

### Issue 3: Statcast Scraper Gets No Data
**Cause:** MLB AM ID mapping failed
**Solution:**
- Check player names are formatted correctly
- Try alternative name spellings
- Some players may not have Statcast data

### Issue 4: Dashboard Loads Slowly
**Cause:** Large dataset, no query optimization
**Solution:**
```python
# In dashboard/app.py
@st.cache_data(ttl=600)  # Increase cache time to 10 minutes

# Or add database indexes
CREATE INDEX idx_season_stats_season_pa ON season_stats(season, pa);
```

### Issue 5: Dashboard Shows No Data
**Cause:** Database connection issue
**Solution:**
```bash
# Test database connection
python -c "from src.utils.db_connection import get_session; print(get_session())"

# Check .env file
cat .env
```

---

## Performance Optimization

### Database Indexes
```sql
-- Add these if not already present
CREATE INDEX IF NOT EXISTS idx_season_stats_player_season ON season_stats(player_id, season);
CREATE INDEX IF NOT EXISTS idx_statcast_player_season ON statcast_data(player_id, season);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
```

### Query Optimization
```sql
-- Use EXPLAIN ANALYZE to check query performance
EXPLAIN ANALYZE
SELECT p.name, ss.wrc_plus
FROM players p
JOIN season_stats ss ON p.player_id = ss.player_id
WHERE ss.season = 2025
  AND ss.pa >= 100;
```

### Dashboard Performance
- Increase cache TTL for static data
- Limit result sizes (top 100 players)
- Use pagination for large tables
- Optimize SQL queries

---

## Rollback Procedures

### Rollback Player Additions
```sql
-- Remove newly added players
DELETE FROM season_stats
WHERE player_id IN (
    SELECT player_id FROM players
    WHERE created_at > '2026-02-13'
);

DELETE FROM players
WHERE created_at > '2026-02-13';
```

### Rollback Statcast Data
```sql
-- Remove all Statcast data
TRUNCATE TABLE statcast_data;
```

### Rollback Schema Changes
```sql
-- Remove new columns from statcast_data
ALTER TABLE statcast_data
DROP COLUMN IF EXISTS max_exit_velo,
DROP COLUMN IF EXISTS ev_90th_percentile,
...;

-- Remove new tables
DROP TABLE IF EXISTS defensive_stats;
DROP TABLE IF EXISTS baserunning_stats;
DROP TABLE IF EXISTS situational_splits;
```

---

## Maintenance

### Daily Updates
```bash
# Update stats for all players (existing script)
python src/automation/daily_scraper.py

# Update Statcast data (add new script or modify daily_scraper.py)
```

### Weekly Tasks
- Review regression signals
- Check for new players (rookies, call-ups)
- Validate prediction accuracy

### Monthly Tasks
- Backup database
- Review and clean failed player loads
- Update season ranges as needed

---

## Success Criteria

### Phase 1 ✅
- [ ] 400+ players in database
- [ ] <5% load failure rate
- [ ] Full 2015-2025 coverage

### Phase 2A ✅
- [ ] Statcast data for 300+ players
- [ ] Enhanced regression detection working
- [ ] Statcast signals in reports

### Phase 3 ✅
- [ ] Dashboard launches successfully
- [ ] All pages functional
- [ ] Charts render correctly
- [ ] Data loads in <3 seconds

---

## Next Steps After Implementation

1. **Run Daily Updates** - Set up automated daily scraper
2. **Evaluate Predictions** - Track prediction accuracy over time
3. **Expand Features** - Add team analytics, player comparisons
4. **Share Dashboard** - Deploy to cloud for remote access
5. **Advanced Analytics** - Implement ML models, clustering

---

## Support & Resources

### Documentation
- `EXPANSION_PLAN.md` - High-level roadmap
- `PYBASEBALL_INTEGRATION.md` - Pybaseball usage details
- `dashboard/README.md` - Dashboard-specific guide

### External Resources
- pybaseball docs: https://github.com/jldbc/pybaseball
- Streamlit docs: https://docs.streamlit.io
- FanGraphs glossary: https://library.fangraphs.com

### Troubleshooting
1. Check logs in terminal
2. Review progress JSON files
3. Test database connection independently
4. Verify API access (pybaseball, Baseball Savant)

---

## Conclusion

Following this guide, you should be able to:
1. **Expand player database** from 53 to 500+ players (Phase 1)
2. **Add Statcast metrics** for enhanced predictions (Phase 2A)
3. **Launch dashboard** for interactive analysis (Phase 3)

**Total implementation time:** 6-10 hours

**Result:** Production-grade baseball analytics platform with comprehensive data coverage and professional visualization.
