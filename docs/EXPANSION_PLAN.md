# Baseball Analytics Expansion Plan

## Overview
This document outlines the roadmap for expanding the baseball analytics platform across three key areas:
1. **Player Database Expansion** - From 53 to 500+ active MLB players
2. **Enhanced Data Sources** - Add Statcast, Baseball-Reference, and advanced metrics
3. **UI/Dashboard Development** - Build visualization and analysis interface

---

## Phase 1: Player Database Expansion (Immediate - Week 1)

### Goal
Expand from 53 to 500+ active MLB players with minimal manual effort.

### Strategy
Use pybaseball's `batting_stats()` to automatically discover all qualified players.

### Implementation Tasks

#### Task 1.1: Create Bulk Player Discovery Script
**File:** `src/scripts/discover_all_active_players.py`
- Fetch all players with min 50 PA from 2023-2025
- Automatically lookup FanGraphs IDs via pybaseball
- Filter for active players (played in 2024 or 2025)
- Export to verification file

**Expected Output:** 400-600 active MLB players

#### Task 1.2: Create Batch Loading Script
**File:** `src/scripts/load_all_active_players_batch.py`
- Load discovered players in batches of 50
- Progress tracking with resume capability
- Error handling and retry logic
- Rate limiting to avoid API blocks

#### Task 1.3: Database Optimization
- Add indexes for performance with larger dataset
- Optimize queries for 10x more players
- Add player status tracking (active, injured, retired)

**Timeline:** 3-5 days

---

## Phase 2: Enhanced Data Sources (Weeks 2-3)

### 2A: Statcast Integration (HIGH PRIORITY)

#### Why Statcast?
Statcast provides the most predictive metrics for player performance:
- Exit velocity (correlates better with future HR than current HR)
- Hard-hit % (more stable than BABIP)
- Barrel % (best predictor of sustainable power)
- Launch angle (identifies optimal contact)
- Expected stats (xBA, xSLG, xwOBA)

#### Implementation

**Task 2A.1: Statcast Data Fetcher**
**File:** `src/scrapers/statcast_scraper.py`

Features:
- Use pybaseball's `statcast_batter()` for raw data
- Aggregate to season-level metrics
- Handle MLB AM ID mapping (different from FanGraphs ID)
- Calculate custom metrics (sweet spot %, chase rate, etc.)

**Task 2A.2: Populate Statcast Table**
**File:** `src/scripts/populate_statcast_data.py`

Process:
1. Map FanGraphs IDs to MLB AM IDs via pybaseball
2. Fetch Statcast data for 2020-2025 (Statcast started 2015, but quality improved)
3. Calculate aggregated metrics per player-season
4. Insert into `statcast_data` table

**Task 2A.3: Enhanced Regression Detection**
**Update:** `src/analytics/regression_detector.py`

New signals:
- Hard-hit% vs BABIP divergence (unlucky vs lucky)
- Exit velo decline (age-related skill loss)
- Barrel% sustainability check
- Launch angle optimization

**Expected Impact:** 
- 30% better prediction accuracy
- Earlier identification of breakouts/declines
- More confident BUY/SELL signals

---

### 2B: Baseball-Reference Integration (MEDIUM PRIORITY)

#### Why Baseball-Reference?
Adds complementary data:
- Accurate birth dates and ages
- Defensive metrics (DRS, UZR)
- Baserunning stats (SB, CS, BsR)
- Situational splits (vs LHP/RHP, home/away)
- Career earnings and contract data

#### Implementation

**Task 2B.1: Baseball-Reference Scraper**
**File:** `src/scrapers/baseball_reference.py`

Data to fetch:
- Player biographical data (birth date, position, bats/throws)
- Defensive metrics by position
- Baserunning value (BsR)
- Situational splits

**Task 2B.2: Expand Database Schema**
**File:** `src/database/schema_expansion.sql`

New tables:
```sql
-- Defensive stats
CREATE TABLE defensive_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    position VARCHAR(10),
    innings DECIMAL(6,1),
    drs INTEGER,        -- Defensive Runs Saved
    uzr DECIMAL(5,1),   -- Ultimate Zone Rating
    outs_above_avg INTEGER,
    UNIQUE(player_id, season, position)
);

-- Baserunning stats
CREATE TABLE baserunning_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    sb INTEGER,
    cs INTEGER,
    bsr DECIMAL(5,1),   -- Baserunning Runs
    UNIQUE(player_id, season)
);

-- Situational splits
CREATE TABLE situational_splits (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(player_id),
    season INTEGER NOT NULL,
    split_type VARCHAR(20),  -- 'vs_lhp', 'vs_rhp', 'home', 'away'
    pa INTEGER,
    avg DECIMAL(5,3),
    obp DECIMAL(5,3),
    slg DECIMAL(5,3),
    woba DECIMAL(5,3),
    UNIQUE(player_id, season, split_type)
);
```

**Task 2B.3: Enhanced Predictive Model**
**Update:** `src/analytics/predictive_model.py`

New prediction components:
- Defense-adjusted value (WAR calculation)
- Position scarcity adjustment
- Platoon split analysis
- Baserunning value projection

---

### 2C: Advanced FanGraphs Metrics (LOW PRIORITY)

#### Additional Metrics to Add
Current coverage: Basic batting stats + wRC+, BABIP, K%, BB%, ISO

**Add:**
- Plate discipline: O-Swing%, Z-Swing%, SwStr%, Contact%
- Quality of contact: Pull%, Cent%, Oppo%
- Speed: Sprint speed, SB%, CS%
- Batted ball: Soft%, Med%, Hard%
- Pitch type values: wFB, wSL, wCH, wCU

**Implementation:**
**File:** `src/scrapers/fangraphs_advanced.py`

Use FanGraphs leaderboards with expanded stat groups:
- Batted Ball
- Plate Discipline
- Pitch Type
- Speed/Base Running

---

## Phase 3: UI/Dashboard Development (Weeks 4-6)

### 3A: Technology Stack Selection

#### Option 1: Streamlit (RECOMMENDED for MVP)
**Pros:**
- Pure Python (no JS/HTML required)
- Rapid development (build dashboard in days)
- Built-in components for tables, charts, filters
- Easy deployment

**Cons:**
- Limited customization
- Not ideal for complex interactivity

**Use case:** Quick MVP to visualize data and test features

#### Option 2: Flask + React/Vue
**Pros:**
- Full control over UI/UX
- Professional-grade application
- Better performance at scale

**Cons:**
- Requires frontend development (JavaScript)
- Longer development time

**Use case:** Production-grade application for external use

#### Option 3: Plotly Dash
**Pros:**
- More customizable than Streamlit
- Still Python-based
- Better interactivity

**Cons:**
- Steeper learning curve than Streamlit
- More verbose code

**Recommendation:** **Start with Streamlit for MVP**, migrate to Flask+React if needed later.

---

### 3B: Dashboard Features (Prioritized)

#### MVP Features (Week 4)

**Feature 1: Player Search & Overview**
- Search bar for player lookup
- Player card with key stats (wRC+, HR, OPS)
- Career trajectory chart
- Recent season comparison

**Feature 2: Regression Signals Dashboard**
- Table of all players with BUY/SELL signals
- Filterable by signal strength (Tier 1, Tier 2)
- Sort by net regression score
- Drill-down to see detailed metrics

**Feature 3: Predictive Model Viewer**
- 2026 projections table
- Comparison: Predicted vs Baseline vs Current
- Confidence intervals visualization
- Component breakdown (age, discipline, power, etc.)

**Feature 4: League Comparison**
- Percentile charts for any player
- Compare multiple players side-by-side
- Position-based filtering

#### Advanced Features (Weeks 5-6)

**Feature 5: Statcast Visualizations**
- Exit velocity distribution
- Launch angle spray charts
- Barrel zone heatmaps
- Hard-hit % trends over time

**Feature 6: Custom Analytics**
- Build your own stat comparisons
- Export data to CSV
- Save favorite players
- Alert notifications for regression signals

**Feature 7: Team Analytics**
- Team-level aggregations
- Roster construction analysis
- Value identification (undervalued players)

---

### 3C: Implementation Plan

#### Step 1: Project Setup
**File Structure:**
```
dashboard/
├── app.py                 # Main Streamlit app
├── pages/
│   ├── 1_player_search.py
│   ├── 2_regression_signals.py
│   ├── 3_predictions.py
│   ├── 4_statcast_viz.py
│   └── 5_league_comparison.py
├── components/
│   ├── player_card.py
│   ├── stat_table.py
│   ├── charts.py
│   └── filters.py
└── utils/
    ├── data_loader.py
    └── formatters.py
```

#### Step 2: Core Components
- Database connection pooling
- Caching for performance (Streamlit's @st.cache_data)
- Responsive layouts
- Theme customization

#### Step 3: Visualization Library
Use **Plotly** for interactive charts:
- Line charts (career trajectories)
- Scatter plots (exit velo vs launch angle)
- Bar charts (percentile comparisons)
- Heatmaps (spray charts)

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Player Expansion** | Week 1 | 500+ players in database |
| **Phase 2A: Statcast** | Week 2 | Statcast data integrated, enhanced predictions |
| **Phase 2B: Baseball-Ref** | Week 3 | Defensive/baserunning data, expanded schema |
| **Phase 3: Dashboard MVP** | Week 4 | Streamlit app with core features |
| **Phase 3: Advanced Dashboard** | Weeks 5-6 | Statcast viz, custom analytics |

**Total Timeline:** 6 weeks for complete implementation

---

## Success Metrics

### Phase 1
- ✅ 400+ active players loaded
- ✅ <5% data fetch failure rate
- ✅ Full 2015-2025 history for each player

### Phase 2
- ✅ Statcast data for 2020-2025 (all players with 100+ PA)
- ✅ 15-20% improvement in prediction accuracy
- ✅ Defense/baserunning data for position players

### Phase 3
- ✅ Dashboard loads in <3 seconds
- ✅ All core features functional
- ✅ Mobile-responsive design
- ✅ Export functionality working

---

## Risk Mitigation

### Risk 1: API Rate Limiting
**Mitigation:**
- Implement aggressive caching
- Add delays between requests (2-3 seconds)
- Use batch processing with resume capability
- Store raw data locally to avoid re-fetching

### Risk 2: Data Quality Issues
**Mitigation:**
- Validation checks before database insertion
- Manual review of outliers
- Logging of failed fetches for later retry

### Risk 3: Performance with Large Dataset
**Mitigation:**
- Database indexing on key columns
- Query optimization (EXPLAIN ANALYZE)
- Dashboard caching
- Pagination for large result sets

### Risk 4: MLB AM ID Mapping
**Mitigation:**
- Use pybaseball's built-in ID mapping
- Fallback to manual mapping for edge cases
- Store multiple ID types in database

---

## Next Steps

### Immediate Actions (Today)
1. ✅ Review and approve expansion plan
2. Create `discover_all_active_players.py` script
3. Test with small batch (10-20 players)
4. Run full player discovery

### Week 1 Actions
1. Complete player database expansion
2. Verify data quality
3. Begin Statcast integration planning

### Dependencies to Install
```bash
pip install streamlit plotly
```

---

## Questions for Discussion

1. **Player Count Target:** Should we include minor league prospects or strictly MLB active?
2. **Statcast Years:** Focus on 2020-2025 or full history back to 2015?
3. **Dashboard Deployment:** Local use only or deploy to cloud (Streamlit Cloud, Heroku)?
4. **Update Frequency:** Real-time daily updates or manual refresh?
5. **User Access:** Personal use or shared with others?

---

## Conclusion

This expansion will transform your analytics platform from a proof-of-concept (53 players) to a production-grade system (500+ players, multi-source data, interactive dashboard). The phased approach ensures continuous progress while managing risk.

**Estimated Total Effort:** 60-80 hours over 6 weeks
**ROI:** 10x more players, 2x better predictions, professional visualization
