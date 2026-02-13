"""
Baseball Analytics Dashboard

Interactive dashboard for exploring player data, predictions, and regression signals.
Built with Streamlit for rapid prototyping.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text

from src.utils.db_connection import get_session
from src.analytics.predictive_model import AdvancedPerformancePredictor
from src.analytics.regression_detector import RegressionDetector

# Page config
st.set_page_config(
    page_title="Baseball Analytics Dashboard",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stAlert > div {
        padding: 1rem;
    }
    h1 {
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_players():
    """Load all players from database"""
    session = get_session()
    
    try:
        query = text("""
            SELECT p.player_id, p.name, p.fg_id, 
                   COUNT(DISTINCT ss.season) as seasons,
                   MAX(ss.season) as last_season
            FROM players p
            LEFT JOIN season_stats ss ON p.player_id = ss.player_id
            GROUP BY p.player_id, p.name, p.fg_id
            ORDER BY p.name
        """)
        
        df = pd.read_sql(query, session.bind)
        return df
        
    finally:
        session.close()


@st.cache_data(ttl=300)
def load_player_stats(player_id):
    """Load all stats for a player"""
    session = get_session()
    
    try:
        query = text("""
            SELECT ss.season, ss.team, ss.games, ss.pa, ss.ab, ss.hits,
                   ss.hr, ss.rbi, ss.bb, ss.so,
                   ss.avg, ss.obp, ss.slg, ss.woba, ss.wrc_plus,
                   ss.babip, ss.k_pct, ss.bb_pct, ss.iso, ss.hr_fb_pct
            FROM season_stats ss
            WHERE ss.player_id = :player_id
            ORDER BY ss.season
        """)
        
        df = pd.read_sql(query, session.bind, params={'player_id': player_id})
        return df
        
    finally:
        session.close()


@st.cache_data(ttl=300)
def load_statcast_data(player_id):
    """Load Statcast data for a player"""
    session = get_session()
    
    try:
        query = text("""
            SELECT season, exit_velo, launch_angle, hard_hit_pct, barrel_pct,
                   sweet_spot_pct, xba, xslg, xwoba
            FROM statcast_data
            WHERE player_id = :player_id
            ORDER BY season
        """)
        
        df = pd.read_sql(query, session.bind, params={'player_id': player_id})
        return df
        
    finally:
        session.close()


@st.cache_data(ttl=300)
def load_regression_signals(season=2025):
    """Load regression signals for all players"""
    detector = RegressionDetector()
    session = get_session()
    
    try:
        query = text("""
            SELECT p.player_id, p.name, ss.team
            FROM players p
            JOIN season_stats ss ON p.player_id = ss.player_id
            WHERE ss.season = :season
              AND ss.pa >= 100
        """)
        
        players = session.execute(query, {'season': season}).fetchall()
        
        results = []
        for player_id, name, team in players:
            analysis = detector.analyze_player_season(player_id, season)
            
            if analysis and analysis['alerts']:
                results.append({
                    'player_id': player_id,
                    'name': name,
                    'team': team,
                    'net_score': analysis['net_score'],
                    'tier1_buys': analysis['tier1_buys'],
                    'tier1_sells': analysis['tier1_sells'],
                    'alerts': analysis['alerts']
                })
        
        return pd.DataFrame(results)
        
    finally:
        session.close()


def main():
    """Main dashboard"""
    
    # Sidebar
    st.sidebar.title("⚾ Baseball Analytics")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "👤 Player Search", "📊 Regression Signals", "🔮 Predictions", "📈 League Stats"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Tip:** Use filters to narrow down results")
    
    # Main content
    if page == "🏠 Home":
        show_home()
    elif page == "👤 Player Search":
        show_player_search()
    elif page == "📊 Regression Signals":
        show_regression_signals()
    elif page == "🔮 Predictions":
        show_predictions()
    elif page == "📈 League Stats":
        show_league_stats()


def show_home():
    """Home page with overview"""
    st.title("⚾ Baseball Analytics Dashboard")
    st.markdown("### Advanced MLB Player Analysis & Predictions")
    
    # Load stats
    players_df = load_players()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Players", len(players_df))
    
    with col2:
        total_seasons = players_df['seasons'].sum()
        st.metric("Player-Seasons", total_seasons)
    
    with col3:
        active_players = len(players_df[players_df['last_season'] >= 2024])
        st.metric("Active Players (2024+)", active_players)
    
    with col4:
        avg_seasons = players_df['seasons'].mean()
        st.metric("Avg Seasons/Player", f"{avg_seasons:.1f}")
    
    st.markdown("---")
    
    # Features
    st.markdown("## 🎯 Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📊 **Analytics**
        - Regression detection (BABIP, K%, BB%, ISO, HR/FB%)
        - Advanced predictions with aging curves
        - Role classification (9 usage-based roles)
        - League percentile comparisons
        """)
        
        st.markdown("""
        ### 🔮 **Predictions**
        - Multi-component 2026 projections
        - Age adjustments
        - Skill change detection
        - Confidence intervals
        """)
    
    with col2:
        st.markdown("""
        ### 📈 **Data Sources**
        - FanGraphs batting stats (2015-2025)
        - Statcast metrics (2020-2025)
        - Historical trends & trajectories
        """)
        
        st.markdown("""
        ### 🚨 **Alerts**
        - BUY/SELL recommendations
        - Tier-based signal strength
        - Detailed explanations
        """)
    
    st.markdown("---")
    
    # Quick start
    st.markdown("## 🚀 Quick Start")
    st.markdown("""
    1. **Player Search**: Look up any player and view detailed stats
    2. **Regression Signals**: Find buy/sell candidates
    3. **Predictions**: See 2026 projections
    4. **League Stats**: Compare players league-wide
    """)


def show_player_search():
    """Player search and detail view"""
    st.title("👤 Player Search")
    
    # Load players
    players_df = load_players()
    
    # Search
    search = st.text_input("🔍 Search player name", "")
    
    if search:
        filtered = players_df[players_df['name'].str.contains(search, case=False)]
    else:
        filtered = players_df
    
    # Select player
    if not filtered.empty:
        selected_name = st.selectbox("Select Player", filtered['name'].tolist())
        
        if selected_name:
            player_id = filtered[filtered['name'] == selected_name]['player_id'].iloc[0]
            
            # Load data
            stats_df = load_player_stats(player_id)
            statcast_df = load_statcast_data(player_id)
            
            # Display player info
            st.markdown(f"## {selected_name}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Seasons", len(stats_df))
            with col2:
                st.metric("Career PA", stats_df['pa'].sum())
            with col3:
                if not stats_df.empty:
                    career_wrc = stats_df['wrc_plus'].mean()
                    st.metric("Career wRC+", f"{career_wrc:.0f}")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Stats", "📈 Trends", "🎯 Statcast", "🔮 Prediction"])
            
            with tab1:
                show_player_stats(stats_df)
            
            with tab2:
                show_player_trends(stats_df)
            
            with tab3:
                show_player_statcast(statcast_df, stats_df)
            
            with tab4:
                show_player_prediction(player_id, selected_name)


def show_player_stats(stats_df):
    """Display player stats table"""
    if stats_df.empty:
        st.warning("No stats available")
        return
    
    # Format display
    display_df = stats_df[['season', 'team', 'games', 'pa', 'avg', 'obp', 'slg', 
                           'hr', 'rbi', 'bb', 'so', 'wrc_plus', 'babip', 'iso']].copy()
    
    # Format decimals
    for col in ['avg', 'obp', 'slg', 'babip', 'iso']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "-")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def show_player_trends(stats_df):
    """Display career trajectory charts"""
    if stats_df.empty:
        st.warning("No stats available")
        return
    
    # wRC+ over time
    fig = px.line(stats_df, x='season', y='wrc_plus', 
                  title='wRC+ Career Trajectory',
                  markers=True)
    fig.add_hline(y=100, line_dash="dash", line_color="gray", 
                  annotation_text="League Average")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Key metrics
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(stats_df, x='season', y=['k_pct', 'bb_pct'],
                     title='Plate Discipline',
                     labels={'value': 'Percentage', 'variable': 'Metric'})
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(stats_df, x='season', y=['babip', 'iso'],
                     title='BABIP & ISO',
                     labels={'value': 'Rate', 'variable': 'Metric'})
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def show_player_statcast(statcast_df, stats_df):
    """Display Statcast metrics"""
    if statcast_df.empty:
        st.warning("No Statcast data available")
        return
    
    st.markdown("### Statcast Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    latest = statcast_df.iloc[-1]
    
    with col1:
        st.metric("Avg Exit Velo", f"{latest['exit_velo']:.1f} mph" if pd.notna(latest['exit_velo']) else "-")
    with col2:
        st.metric("Hard-Hit%", f"{latest['hard_hit_pct']:.1f}%" if pd.notna(latest['hard_hit_pct']) else "-")
    with col3:
        st.metric("Barrel%", f"{latest['barrel_pct']:.1f}%" if pd.notna(latest['barrel_pct']) else "-")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(statcast_df, x='season', y='exit_velo',
                     title='Exit Velocity Trend',
                     markers=True)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(statcast_df, x='season', y=['hard_hit_pct', 'barrel_pct'],
                     title='Contact Quality',
                     labels={'value': 'Percentage', 'variable': 'Metric'})
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Expected vs Actual
    if not stats_df.empty and 'xwoba' in statcast_df.columns:
        merged = pd.merge(stats_df[['season', 'woba']], 
                         statcast_df[['season', 'xwoba']], 
                         on='season')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged['season'], y=merged['woba'],
                                name='Actual wOBA', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=merged['season'], y=merged['xwoba'],
                                name='Expected wOBA', mode='lines+markers',
                                line=dict(dash='dash')))
        fig.update_layout(title='wOBA vs xwOBA', height=300)
        st.plotly_chart(fig, use_container_width=True)


def show_player_prediction(player_id, player_name):
    """Display prediction for player"""
    predictor = AdvancedPerformancePredictor()
    
    pred = predictor.predict_next_season_advanced(player_id, 2025)
    
    if not pred:
        st.warning("Insufficient data for prediction")
        return
    
    st.markdown("### 2026 Projection")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Projected wRC+", pred['predicted_wrc'])
    with col2:
        st.metric("Range", f"{pred['prediction_range'][0]}-{pred['prediction_range'][1]}")
    with col3:
        st.metric("Confidence", pred['confidence'])
    
    # Component breakdown
    st.markdown("#### Adjustment Breakdown")
    
    components = pd.DataFrame({
        'Component': ['Baseline', 'Age', 'Discipline', 'Power', 'Contact', 'Skill Change', 'Regression'],
        'Adjustment': [pred['baseline_wrc'], pred['age_adjustment'], pred['discipline_adjustment'],
                      pred['power_adjustment'], pred['contact_adjustment'], 
                      pred['skill_change_adjustment'], pred['regression_adjustment']]
    })
    
    fig = px.bar(components, x='Component', y='Adjustment',
                title='Prediction Components',
                color='Adjustment',
                color_continuous_scale='RdYlGn')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Details
    with st.expander("📊 Detailed Breakdown"):
        st.markdown(f"**Age Profile:** {pred['current_age']} → {pred['next_age']}")
        st.markdown(f"**Contact Type:** {pred['contact_type']}")
        st.markdown(f"**Sample Size:** {pred['sample_size_pa']} PA over {pred['recent_seasons']} seasons")
        
        if pred['power_flags']:
            st.markdown("**Power Flags:**")
            for flag in pred['power_flags']:
                st.markdown(f"- ⚠️ {flag}")


def show_regression_signals():
    """Display regression signals page"""
    st.title("📊 Regression Signals")
    st.markdown("### BUY/SELL Recommendations")
    
    # Load signals
    with st.spinner("Analyzing regression signals..."):
        signals_df = load_regression_signals(2025)
    
    if signals_df.empty:
        st.warning("No regression signals found")
        return
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        signal_type = st.selectbox("Signal Type", ["All", "SELL", "BUY"])
    with col2:
        min_score = st.slider("Minimum |Net Score|", 0, 5, 2)
    
    # Filter
    filtered = signals_df.copy()
    
    if signal_type != "All":
        if signal_type == "SELL":
            filtered = filtered[filtered['net_score'] <= -min_score]
        else:
            filtered = filtered[filtered['net_score'] >= min_score]
    else:
        filtered = filtered[abs(filtered['net_score']) >= min_score]
    
    # Sort
    filtered = filtered.sort_values('net_score')
    
    st.markdown(f"### {len(filtered)} Players with Signals")
    
    # Display
    for _, row in filtered.iterrows():
        signal_color = "🔴" if row['net_score'] < 0 else "🟢"
        
        with st.expander(f"{signal_color} {row['name']} ({row['team']}) - Net: {row['net_score']:.1f}"):
            for alert in row['alerts']:
                tier_emoji = "🔴" if alert['tier'] == 1 and alert['signal'] == 'SELL' else \
                            "🟢" if alert['tier'] == 1 and alert['signal'] == 'BUY' else "🟡"
                
                st.markdown(f"{tier_emoji} **Tier {alert['tier']} {alert['metric']}**: {alert['explanation']}")


def show_league_stats():
    """Display league-wide statistics"""
    st.title("📈 League Statistics")
    
    session = get_session()
    
    try:
        # Load 2025 stats
        query = text("""
            SELECT p.name, ss.team, ss.pa, ss.wrc_plus, ss.avg, ss.obp, ss.slg,
                   ss.hr, ss.rbi, ss.babip, ss.iso, ss.k_pct, ss.bb_pct
            FROM season_stats ss
            JOIN players p ON ss.player_id = p.player_id
            WHERE ss.season = 2025
              AND ss.pa >= 100
            ORDER BY ss.wrc_plus DESC
        """)
        
        df = pd.read_sql(query, session.bind)
        
        if df.empty:
            st.warning("No data available")
            return
        
        st.markdown(f"### 2025 Season ({len(df)} qualified players)")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Avg wRC+", f"{df['wrc_plus'].mean():.0f}")
        with col2:
            st.metric("Avg BA", f"{df['avg'].mean():.3f}")
        with col3:
            st.metric("Avg OBP", f"{df['obp'].mean():.3f}")
        with col4:
            st.metric("Avg SLG", f"{df['slg'].mean():.3f}")
        
        # Leaderboard
        st.markdown("### wRC+ Leaderboard")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
