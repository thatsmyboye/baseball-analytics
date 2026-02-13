"""
Historical Trend Tracker

Track player performance trends over time:
- Multi-season progression/regression
- Career arcs and aging curves
- Hot/cold streaks detection
- Breakout/bounce-back identification
"""
import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db_connection import get_session

class TrendTracker:
    """
    Analyze historical trends and career trajectories
    """
    
    def __init__(self):
        pass
    
    def get_player_career_trajectory(self, player_id):
        """
        Get full career trajectory for a player
        
        Returns:
            DataFrame with year-over-year changes
        """
        session = get_session()
        
        try:
            query = text("""
                SELECT 
                    season, team, games, pa,
                    avg, obp, slg, wrc_plus, babip,
                    bb_pct, k_pct, iso, hr
                FROM season_stats
                WHERE player_id = :player_id
                  AND pa >= 50
                ORDER BY season
            """)
            
            df = pd.read_sql(query, session.bind, params={'player_id': player_id})
            
            if df.empty:
                return None
            
            # Calculate year-over-year changes
            df['yoy_wrc_plus'] = df['wrc_plus'].diff()
            df['yoy_babip'] = df['babip'].diff()
            df['yoy_k_pct'] = df['k_pct'].diff()
            df['yoy_bb_pct'] = df['bb_pct'].diff()
            df['yoy_iso'] = df['iso'].diff()
            
            # Calculate rolling averages (3-year)
            df['wrc_plus_3yr'] = df['wrc_plus'].rolling(window=3, min_periods=1).mean()
            df['babip_3yr'] = df['babip'].rolling(window=3, min_periods=1).mean()
            
            return df
        
        finally:
            session.close()
    
    def detect_breakout_season(self, player_id, season):
        """
        Identify if a season represents a breakout
        
        Criteria:
        - Significant wRC+ improvement (>20 points)
        - Sustained over full season (400+ PA)
        - Not just BABIP-driven luck
        
        Returns:
            dict with breakout analysis
        """
        trajectory = self.get_player_career_trajectory(player_id)
        
        if trajectory is None or season not in trajectory['season'].values:
            return None
        
        current = trajectory[trajectory['season'] == season].iloc[0]
        previous = trajectory[trajectory['season'] < season]
        
        if previous.empty:
            return None
        
        # Get previous 3 years average (or career if less than 3 years)
        baseline_wrc = previous['wrc_plus'].tail(3).mean()
        baseline_babip = previous['babip'].tail(3).mean()
        
        # Calculate improvements
        wrc_improvement = current['wrc_plus'] - baseline_wrc
        babip_change = current['babip'] - baseline_babip
        k_improvement = baseline_wrc  # Use previous for K% comparison
        
        # Determine if breakout
        is_breakout = (
            wrc_improvement >= 20 and
            current['pa'] >= 400 and
            babip_change < 0.040  # Not purely BABIP-driven
        )
        
        return {
            'is_breakout': is_breakout,
            'wrc_improvement': wrc_improvement,
            'baseline_wrc': baseline_wrc,
            'current_wrc': current['wrc_plus'],
            'babip_change': babip_change,
            'pa': current['pa'],
            'confidence': 'HIGH' if is_breakout and babip_change < 0.020 else 'MEDIUM'
        }
    
    def detect_decline_trend(self, player_id, lookback_years=3):
        """
        Detect if player is on a declining trajectory
        
        Returns:
            dict with decline analysis
        """
        trajectory = self.get_player_career_trajectory(player_id)
        
        if trajectory is None or len(trajectory) < 3:
            return None
        
        recent = trajectory.tail(lookback_years)
        
        # Check for consistent decline in wRC+
        wrc_trend = recent['wrc_plus'].values
        
        # Linear regression to detect trend
        years = np.arange(len(wrc_trend))
        slope = np.polyfit(years, wrc_trend, 1)[0]
        
        # Check if power is declining (ISO trend)
        iso_trend = recent['iso'].values
        iso_slope = np.polyfit(years, iso_trend, 1)[0]
        
        # Check if contact is declining (K% trend)
        k_trend = recent['k_pct'].values
        k_slope = np.polyfit(years, k_trend, 1)[0]
        
        is_declining = slope < -5  # Losing >5 wRC+ points per year
        
        return {
            'is_declining': is_declining,
            'wrc_slope': slope,
            'iso_slope': iso_slope,
            'k_slope': k_slope,
            'recent_avg_wrc': wrc_trend.mean(),
            'trend_strength': abs(slope),
            'years_analyzed': len(wrc_trend)
        }
    
    def identify_career_peak(self, player_id):
        """
        Identify player's career peak season(s)
        
        Returns:
            dict with peak info
        """
        trajectory = self.get_player_career_trajectory(player_id)
        
        if trajectory is None or trajectory.empty:
            return None
        
        # Filter to meaningful seasons (200+ PA)
        meaningful = trajectory[trajectory['pa'] >= 200].copy()
        
        if meaningful.empty:
            return None
        
        # Find peak wRC+ season
        peak_season = meaningful.loc[meaningful['wrc_plus'].idxmax()]
        
        # Check if currently at peak
        latest_season = meaningful.iloc[-1]
        at_peak = (latest_season['wrc_plus'] >= peak_season['wrc_plus'] * 0.95)
        
        # Years since peak
        years_since_peak = latest_season['season'] - peak_season['season']
        
        return {
            'peak_season': int(peak_season['season']),
            'peak_wrc_plus': int(peak_season['wrc_plus']),
            'peak_pa': int(peak_season['pa']),
            'current_season': int(latest_season['season']),
            'current_wrc_plus': int(latest_season['wrc_plus']),
            'at_peak': at_peak,
            'years_since_peak': int(years_since_peak),
            'career_seasons': len(meaningful)
        }
    
    def calculate_aging_curve(self, player_id):
        """
        Calculate player's aging curve (performance by age)
        
        Returns:
            DataFrame with age-based performance
        """
        session = get_session()
        
        try:
            # Get player birth date to calculate age
            query = text("""
                SELECT 
                    ss.season, ss.pa, ss.wrc_plus, ss.babip, ss.iso,
                    p.birth_date,
                    EXTRACT(YEAR FROM ss.season::text::date) - EXTRACT(YEAR FROM p.birth_date) as age
                FROM season_stats ss
                JOIN players p ON ss.player_id = p.player_id
                WHERE ss.player_id = :player_id
                  AND ss.pa >= 100
                  AND p.birth_date IS NOT NULL
                ORDER BY ss.season
            """)
            
            df = pd.read_sql(query, session.bind, params={'player_id': player_id})
            
            if df.empty:
                return None
            
            return df[['season', 'age', 'pa', 'wrc_plus', 'babip', 'iso']]
        
        finally:
            session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("HISTORICAL TREND TRACKER")
    print("=" * 70)
    
    tracker = TrendTracker()
    
    # Test with Harrison Bader
    session = get_session()
    bader_id = session.execute(
        text("SELECT player_id FROM players WHERE name = 'Harrison Bader'")
    ).fetchone()[0]
    session.close()
    
    print("\n📊 Harrison Bader Career Trajectory...\n")
    
    trajectory = tracker.get_player_career_trajectory(bader_id)
    
    if trajectory is not None:
        print("Year-over-Year Performance:")
        print(trajectory[['season', 'team', 'pa', 'wrc_plus', 'yoy_wrc_plus', 
                         'babip', 'yoy_babip']].to_string(index=False))
        
        # Check for breakout
        print("\n\n🚀 Breakout Analysis (2024)...")
        breakout = tracker.detect_breakout_season(bader_id, 2024)
        if breakout:
            print(f"   Breakout Season: {breakout['is_breakout']}")
            print(f"   wRC+ Change: {breakout['baseline_wrc']:.0f} → {breakout['current_wrc']:.0f} " +
                  f"({breakout['wrc_improvement']:+.0f})")
            print(f"   BABIP Change: {breakout['babip_change']:+.3f}")
            print(f"   Confidence: {breakout['confidence']}")
        
        # Check for decline
        print("\n\n📉 Decline Trend Analysis...")
        decline = tracker.detect_decline_trend(bader_id, lookback_years=3)
        if decline:
            print(f"   Declining: {decline['is_declining']}")
            print(f"   wRC+ Slope: {decline['wrc_slope']:.1f} points/year")
            print(f"   ISO Slope: {decline['iso_slope']:.3f}/year")
            print(f"   Recent Avg wRC+: {decline['recent_avg_wrc']:.0f}")
        
        # Find career peak
        print("\n\n⛰️  Career Peak Analysis...")
        peak = tracker.identify_career_peak(bader_id)
        if peak:
            print(f"   Peak Season: {peak['peak_season']} (wRC+: {peak['peak_wrc_plus']})")
            print(f"   Current: {peak['current_season']} (wRC+: {peak['current_wrc_plus']})")
            print(f"   At Peak: {peak['at_peak']}")
            print(f"   Years Since Peak: {peak['years_since_peak']}")
            print(f"   Total Career Seasons: {peak['career_seasons']}")