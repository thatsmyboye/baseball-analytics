# Baseball Analytics System

A comprehensive MLB player analytics platform with regression detection, performance predictions, and automated insights.

## 🎯 Features

### Analytics Engine
- **Role Classification** - Categorize players into 9 usage-based roles
- **Regression Detection** - Identify players due for performance changes across 5 metrics (BABIP, K%, BB%, ISO, HR/FB%)
- **Advanced Predictions** - Multi-component 2026 projections with aging curves
- **League Percentiles** - Compare players against MLB baselines
- **Historical Trends** - Track career trajectories and detect breakouts/declines

### Automation
- **Daily Updates** - Automated stat refreshes for all players
- **Alert Digests** - Summarized regression signals with BUY/SELL recommendations
- **Progress Tracking** - Resume capability for interrupted jobs

## 📊 Database

**Current Stats:**
- 53 verified MLB players
- 700+ player-seasons (2015-2025)
- Comprehensive batting statistics from FanGraphs

**Schema:**
- `players` - Player metadata with birth dates
- `season_stats` - Season-level batting statistics
- `statcast_data` - Reserved for future Statcast integration

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database (or connection to Railway/similar service)
- pip (latest version recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd baseball-analytics
   ```

2. **Upgrade pip (recommended)**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and replace the placeholder values with your actual database credentials:
   ```
   DATABASE_URL=postgresql://your_username:your_password@your_host:5432/your_database
   ```

   **Examples:**
   - Local PostgreSQL: `postgresql://postgres:mypassword@localhost:5432/baseball`
   - Railway: `postgresql://postgres:password@containers-us-west-xyz.railway.app:5432/railway`

   **Important:** Replace ALL placeholder values (`user`, `password`, `host`, `port`, `database`) with actual credentials.

5. **Initialize the database**
   ```bash
   python -c "from src.utils.db_connection import init_database; init_database()"
   ```

### Troubleshooting

**"ValueError: invalid literal for int() with base 10: 'port'"**
This error occurs when your `.env` file contains placeholder values instead of actual database credentials.

Solution:
1. Open your `.env` file in the project root
2. Replace ALL placeholder values with actual credentials (see step 4 above for examples)
3. Make sure to replace: `user`, `password`, `host`, `port`, and `database` with real values

**"DATABASE_URL not found in environment variables"**
You haven't created a `.env` file yet.

Solution: `cp .env.example .env` then edit with your actual credentials.

**psycopg2-binary installation errors:**
- Ensure pip is up to date: `python -m pip install --upgrade pip`
- The updated requirements.txt uses `psycopg2-binary>=2.9.10` which has better prebuilt wheel support
- On Windows, if issues persist, you may need to install Microsoft Visual C++ Build Tools

## 🚀 Quick Start

### Launch Interactive Dashboard
```bash
# On macOS/Linux
streamlit run dashboard/app.py

# On Windows (if streamlit command not found)
python -m streamlit run dashboard/app.py
```

The dashboard provides an interactive web interface for exploring player stats, predictions, and regression signals.

### Generate Player Report
```bash
python -m src.analytics.player_report
```

### Run Regression Detection
```bash
python -m src.analytics.regression_detector
```

### Create 2026 Predictions
```bash
python -m src.analytics.predictive_model
```

### Daily Update (All Players)
```bash
python -m src.automation.daily_scraper
```

### Generate Alert Digest
```bash
python -m src.automation.alert_digest
```

## 📁 Project Structure
```
baseball-analytics/
├── dashboard/               # Interactive web dashboard
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
├── src/
│   ├── analytics/           # Core analytics modules
│   │   ├── role_classifier.py
│   │   ├── regression_detector.py
│   │   ├── league_baselines.py
│   │   ├── trend_tracker.py
│   │   ├── predictive_model.py
│   │   └── player_report.py
│   ├── automation/          # Daily updates & alerts
│   │   ├── daily_scraper.py
│   │   └── alert_digest.py
│   ├── database/            # Schema & data loading
│   │   ├── schema.sql
│   │   └── insert_data.py
│   ├── scrapers/            # FanGraphs data pipeline
│   │   ├── fangraphs.py
│   │   └── batch_scraper.py
│   ├── utils/               # Database connection
│   │   └── db_connection.py
│   └── scripts/             # Maintenance tools
│       ├── deduplicate_players.py
│       └── add_birth_dates.py
└── requirements.txt
```

## 🔬 Analytics Examples

### Regression Detection Output
```
🔴 STRONG SELL CANDIDATES
  Matt Olson (Braves) - Net: -2
    🔴 TIER 1 BABIP: BABIP 0.333 is +0.059 above career 0.274
    🟡 TIER 2 ISO: ISO 0.212 is -0.056 below career 0.268

🟢 STRONG BUY CANDIDATES
  Anthony Santander (Orioles) - Net: +1
    🔴 TIER 1 BABIP: BABIP 0.218 is -0.092 below career 0.310
```

### 2026 Predictions
```
ADVANCED PREDICTION: Shohei Ohtani (2026)
  Projected wRC+: 174 (Range: 164-184)
  Age Adjustment: -1 (turning 32)
  Power Sustainability: -5 (unsustainable spike)
  Regression Signals: +4 (positive indicators)
  Confidence: HIGH
```

## 🛠️ Tech Stack

- **Database:** PostgreSQL (Railway)
- **Language:** Python 3.12
- **Libraries:** pandas, SQLAlchemy, requests, beautifulsoup4
- **Data Source:** FanGraphs

## ⚠️ Limitations

- 53 players (manually verified FanGraphs IDs)
- Batting stats only (no pitching yet)
- No Statcast data (exit velocity, hard-hit%, etc.)
- No defensive metrics
- FanGraphs ID discovery is manual

## 🚀 Future Enhancements

- Baseball Savant integration for Statcast data
- Pitcher analytics module
- Web dashboard visualization
- REST API for data access
- Advanced ML prediction models
- Injury risk assessment

## 📝 License

Personal project - not for commercial use

## 🙏 Acknowledgments

Data sourced from FanGraphs.com