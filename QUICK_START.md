# Quick Start - Baseball Analytics Expansion

**Get started with the expansion in 3 phases.**

---

## 🚀 Phase 1: Expand Player Database (3-5 hours)

### Discover Players
```bash
python src/scripts/discover_all_active_players.py
```
- Enter 'yes' to use default settings
- Wait 2-3 minutes for discovery
- Review `discovered_active_players.txt`

### Load Players
```bash
python src/scripts/load_discovered_players.py
```
- Confirm to proceed
- Let it run (2-4 hours with rate limiting)
- Can resume if interrupted

**Expected Result:** 500+ players in database

---

## 📊 Phase 2: Add Statcast Data (2-4 hours)

### Update Database
```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Run schema update
\i src/database/schema_statcast_expansion.sql
\q
```

### Fetch Statcast
```bash
python src/scrapers/statcast_scraper.py
```
- Confirm default seasons (2020-2025)
- Let it run (2-4 hours)

### Test Enhanced Regression
```bash
python src/analytics/statcast_regression_detector.py
```

**Expected Result:** Statcast metrics + enhanced BUY/SELL signals

---

## 🎨 Phase 3: Launch Dashboard (5 minutes)

### Install Dependencies
```bash
pip install streamlit plotly
```

### Launch Dashboard
```bash
streamlit run dashboard/app.py
```

**Dashboard opens at:** http://localhost:8501

**Features:**
- 🏠 Home - Overview
- 👤 Player Search - Look up any player
- 📊 Regression Signals - BUY/SELL recommendations
- 🔮 Predictions - 2026 projections
- 📈 League Stats - Leaderboards

---

## 🆘 Troubleshooting

### Player loading fails?
- Check internet connection
- Increase rate limit in code (2 → 3 seconds)
- Resume with same command

### Statcast has no data?
- Normal - not all players have Statcast data
- Expect 60-80% coverage

### Dashboard won't start?
- Check database connection: `echo $DATABASE_URL`
- Install dependencies: `pip install -r requirements.txt`
- Clear cache: Ctrl+C and restart

---

## 📚 Full Documentation

- **EXPANSION_PLAN.md** - Complete roadmap
- **IMPLEMENTATION_GUIDE.md** - Detailed steps
- **EXPANSION_SUMMARY.md** - What was built
- **dashboard/README.md** - Dashboard guide

---

## ✅ Success Checklist

### Phase 1
- [ ] Ran discovery script
- [ ] Reviewed player list
- [ ] Loaded 400+ new players
- [ ] Verified in database

### Phase 2
- [ ] Updated database schema
- [ ] Fetched Statcast data
- [ ] Ran enhanced regression detector
- [ ] Saw Statcast signals

### Phase 3
- [ ] Installed dashboard dependencies
- [ ] Launched dashboard successfully
- [ ] Tested player search
- [ ] Viewed regression signals
- [ ] Checked predictions

---

## 🎯 After Implementation

### Daily
- Run `python src/automation/daily_scraper.py` to update stats

### Weekly
- Review regression signals for BUY/SELL opportunities
- Check prediction accuracy

### Monthly
- Look for new players (rookies, call-ups)
- Backup database

---

**Need help?** Check `IMPLEMENTATION_GUIDE.md` for detailed troubleshooting.

**Ready to start?**
```bash
python src/scripts/discover_all_active_players.py
```

⚾ **Good luck!** 🚀
