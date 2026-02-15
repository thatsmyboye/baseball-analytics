# Baseball Analytics Dashboard

Interactive web dashboard for exploring MLB player analytics, predictions, and regression signals.

## Features

### 🏠 Home
- Overview of database size and coverage
- Quick stats summary
- Feature highlights

### 👤 Player Search
- Search and select any player
- View detailed season-by-season stats
- Career trajectory charts
- Statcast metrics visualization
- 2026 prediction with component breakdown

### 📊 Regression Signals
- BUY/SELL recommendations
- Filter by signal type and strength
- Detailed explanations for each alert
- Tier-based signal classification

### 🔮 Predictions
- Advanced 2026 projections
- Multi-component analysis
- Confidence intervals
- Age adjustments and skill changes

### 📈 League Stats
- League-wide statistics
- wRC+ leaderboards
- Comparison tools

## Installation

### Install Dependencies
```bash
# Upgrade pip first (recommended)
python -m pip install --upgrade pip

# From project root
pip install streamlit plotly

# Or from dashboard folder
pip install -r requirements.txt
```

### Run Dashboard

**On macOS/Linux:**
```bash
# From project root
streamlit run dashboard/app.py

# Or from dashboard folder
streamlit run app.py
```

**On Windows (PowerShell/Command Prompt):**
```bash
# From project root
python -m streamlit run dashboard/app.py

# Or from dashboard folder
python -m streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

> **Why `python -m streamlit`?** On Windows, the `streamlit` executable may not be in your PATH even after installation. Using `python -m streamlit` ensures Python can find the module.

## Usage Tips

### Navigation
Use the sidebar to switch between different views.

### Filters
Most pages include filters to narrow down results:
- Player search by name
- Signal filtering by type and strength
- Season selection

### Caching
Data is cached for 5 minutes to improve performance. If you update the database, either:
1. Wait 5 minutes for cache to expire
2. Refresh the page with Ctrl+R (or Cmd+R on Mac)
3. Click "Clear Cache" in the hamburger menu (top right)

## Deployment

### Local Network Access
To allow other devices on your network to access the dashboard:
```bash
# macOS/Linux
streamlit run app.py --server.address=0.0.0.0

# Windows
python -m streamlit run app.py --server.address=0.0.0.0
```

Then access from other devices using your computer's IP address:
`http://<your-ip>:8501`

### Cloud Deployment

#### Streamlit Cloud (FREE)
1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repo
4. Deploy with one click

**Note:** You'll need to configure database connection for cloud deployment (use Railway connection string).

#### Other Options
- Heroku
- AWS EC2
- Google Cloud Run
- DigitalOcean App Platform

## Configuration

### Database Connection
The dashboard uses the same database connection as the main analytics system (`src/utils/db_connection.py`).

Ensure your `.env` file has the correct DATABASE_URL:
```
DATABASE_URL=postgresql://user:password@host:port/database
```

### Performance Tuning

For large databases (1000+ players):
- Adjust cache TTL in `@st.cache_data(ttl=300)` decorators
- Add pagination to large tables
- Optimize SQL queries with additional indexes

## Customization

### Theme
Edit `.streamlit/config.toml` to customize colors and theme:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Layout
Modify `app.py` to:
- Add new pages
- Change chart types
- Adjust column layouts
- Add custom metrics

## Troubleshooting

### "streamlit is not recognized" (Windows)
If you get the error:
```
streamlit : The term 'streamlit' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

**Solution:** Use `python -m streamlit` instead of just `streamlit`:
```bash
python -m streamlit run dashboard/app.py
```

This happens because the Python Scripts directory isn't in your PATH, or you're in a virtual environment that hasn't been activated properly.

### Dashboard won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify database connection is working
- Check for port conflicts (8501 is default)

### Data not showing
- Verify database has data: `SELECT COUNT(*) FROM players;`
- Check cache - try clearing it
- Review console for error messages

### Slow performance
- Reduce cache TTL for frequently updated data
- Add database indexes
- Limit query result sizes
- Use pagination for large tables

## Future Enhancements

### Planned Features
- [ ] Export to CSV/Excel
- [ ] Custom report builder
- [ ] Player comparison tool
- [ ] Team analytics view
- [ ] Historical "what-if" scenarios
- [ ] Mobile-responsive design improvements
- [ ] User authentication
- [ ] Saved dashboards/favorites

### Advanced Analytics
- [ ] Interactive scatter plots (exit velo vs launch angle)
- [ ] Spray charts
- [ ] Pitch type breakdown
- [ ] Player similarity scores
- [ ] Contract value analysis

## Support

For issues or questions:
1. Check this README
2. Review dashboard logs in terminal
3. Test database connection independently
4. Review Streamlit documentation: https://docs.streamlit.io

## License

Part of the Baseball Analytics project - personal use only.
