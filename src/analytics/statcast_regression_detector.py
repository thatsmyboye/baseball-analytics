"""
Enhanced Regression Detection with Statcast Data

Improves buy/sell signal accuracy by incorporating:
- Exit velocity vs actual power output
- Hard-hit% vs BABIP divergence (luck detection)
- Barrel% sustainability
- Launch angle optimization
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy import text
from src.utils.db_connection import get_session
from src.analytics.regression_detector import RegressionDetector


class StatcastRegressionDetector(RegressionDetector):
    """
    Enhanced regression detector using Statcast metrics
    """
    
    def __init__(self):
        super().__init__()
    
    def get_statcast_data(self, player_id, season):
        """
        Get Statcast data for a player-season
        
        Returns:
            Dict with Statcast metrics, or None
        """
        session = get_session()
        
        try:
            query = text("""
                SELECT 
                    exit_velo, hard_hit_pct, barrel_pct, sweet_spot_pct,
                    xba, xslg, xwoba, batted_balls
                FROM statcast_data
                WHERE player_id = :player_id
                  AND season = :season
            """)
            
            result = session.execute(query, {'player_id': player_id, 'season': season})
            row = result.fetchone()
            
            if row:
                return {
                    'exit_velo': float(row[0]) if row[0] else None,
                    'hard_hit_pct': float(row[1]) if row[1] else None,
                    'barrel_pct': float(row[2]) if row[2] else None,
                    'sweet_spot_pct': float(row[3]) if row[3] else None,
                    'xba': float(row[4]) if row[4] else None,
                    'xslg': float(row[5]) if row[5] else None,
                    'xwoba': float(row[6]) if row[6] else None,
                    'batted_balls': int(row[7]) if row[7] else None
                }
            return None
            
        finally:
            session.close()
    
    def get_career_statcast_baseline(self, player_id, current_season):
        """
        Get career average Statcast metrics (excluding current season)
        
        Returns:
            Dict with career Statcast baselines
        """
        session = get_session()
        
        try:
            query = text("""
                SELECT 
                    AVG(exit_velo) as avg_exit_velo,
                    AVG(hard_hit_pct) as avg_hard_hit_pct,
                    AVG(barrel_pct) as avg_barrel_pct,
                    AVG(sweet_spot_pct) as avg_sweet_spot_pct,
                    COUNT(*) as seasons
                FROM statcast_data
                WHERE player_id = :player_id
                  AND season < :season
                  AND batted_balls >= 50
            """)
            
            result = session.execute(query, {'player_id': player_id, 'season': current_season})
            row = result.fetchone()
            
            if row and row[4] >= 2:  # At least 2 seasons of data
                return {
                    'career_exit_velo': float(row[0]) if row[0] else None,
                    'career_hard_hit_pct': float(row[1]) if row[1] else None,
                    'career_barrel_pct': float(row[2]) if row[2] else None,
                    'career_sweet_spot_pct': float(row[3]) if row[3] else None,
                    'seasons': int(row[4])
                }
            return None
            
        finally:
            session.close()
    
    def detect_lucky_vs_unlucky(self, current_stats, statcast_data, career_baseline):
        """
        Detect luck using Statcast vs actual performance divergence
        
        Key insight: Hard-hit% and xwOBA are more stable than BABIP and actual wOBA
        
        Returns:
            Dict with signal, tier, and explanation
        """
        if not statcast_data or not career_baseline:
            return None
        
        current_babip = current_stats.get('babip')
        career_babip = career_baseline.get('career_babip')
        hard_hit_pct = statcast_data.get('hard_hit_pct')
        career_hard_hit = career_baseline.get('career_hard_hit_pct')
        
        if not all([current_babip, career_babip, hard_hit_pct, career_hard_hit]):
            return None
        
        babip_delta = current_babip - career_babip
        hard_hit_delta = hard_hit_pct - career_hard_hit
        
        # UNLUCKY: Low BABIP but high hard-hit% = BUY
        if babip_delta < -0.040 and hard_hit_delta > 2:
            return {
                'signal': 'BUY',
                'tier': 1,
                'metric': 'STATCAST_UNLUCKY',
                'explanation': f"BABIP {current_babip:.3f} is low but hard-hit% {hard_hit_pct:.1f}% is up {hard_hit_delta:+.1f}% - Unlucky!",
                'confidence': 'HIGH'
            }
        
        # LUCKY: High BABIP but declining hard-hit% = SELL
        elif babip_delta > 0.040 and hard_hit_delta < -2:
            return {
                'signal': 'SELL',
                'tier': 1,
                'metric': 'STATCAST_LUCKY',
                'explanation': f"BABIP {current_babip:.3f} is high but hard-hit% {hard_hit_pct:.1f}% is down {hard_hit_delta:.1f}% - Lucky!",
                'confidence': 'HIGH'
            }
        
        return None
    
    def detect_power_sustainability(self, current_stats, statcast_data, career_baseline):
        """
        Assess power sustainability using exit velocity and barrel%
        
        Returns:
            Dict with signal or None
        """
        if not statcast_data or not career_baseline:
            return None
        
        current_iso = current_stats.get('iso')
        career_iso = career_baseline.get('career_iso')
        exit_velo = statcast_data.get('exit_velo')
        career_exit_velo = career_baseline.get('career_exit_velo')
        barrel_pct = statcast_data.get('barrel_pct')
        career_barrel_pct = career_baseline.get('career_barrel_pct')
        
        if not all([current_iso, career_iso, exit_velo, career_exit_velo, 
                   barrel_pct, career_barrel_pct]):
            return None
        
        iso_delta = current_iso - career_iso
        ev_delta = exit_velo - career_exit_velo
        barrel_delta = barrel_pct - career_barrel_pct
        
        # Power spike NOT backed by Statcast = SELL
        if iso_delta > 0.060 and ev_delta < 0 and barrel_delta < 0:
            return {
                'signal': 'SELL',
                'tier': 1,
                'metric': 'UNSUSTAINABLE_POWER',
                'explanation': f"ISO +{iso_delta:.3f} but EV down {ev_delta:.1f} mph, Barrel% down {barrel_delta:.1f}% - Unsustainable!",
                'confidence': 'HIGH'
            }
        
        # Depressed power WITH good Statcast = BUY
        elif iso_delta < -0.050 and ev_delta > 0 and barrel_delta > 1:
            return {
                'signal': 'BUY',
                'tier': 1,
                'metric': 'UNLUCKY_POWER',
                'explanation': f"ISO down {iso_delta:.3f} but EV up {ev_delta:+.1f} mph, Barrel% up {barrel_delta:+.1f}% - Unlucky power!",
                'confidence': 'HIGH'
            }
        
        return None
    
    def detect_exit_velo_decline(self, statcast_data, career_baseline):
        """
        Detect concerning exit velocity decline (age-related skill loss)
        
        Returns:
            Dict with signal or None
        """
        if not statcast_data or not career_baseline:
            return None
        
        exit_velo = statcast_data.get('exit_velo')
        career_exit_velo = career_baseline.get('career_exit_velo')
        
        if not exit_velo or not career_exit_velo:
            return None
        
        ev_delta = exit_velo - career_exit_velo
        
        # Significant EV decline = SELL (skill deterioration)
        if ev_delta < -2.0:
            return {
                'signal': 'SELL',
                'tier': 2,
                'metric': 'EV_DECLINE',
                'explanation': f"Exit velo down {ev_delta:.1f} mph - Possible skill decline",
                'confidence': 'MEDIUM'
            }
        
        return None
    
    def detect_expected_stats_divergence(self, current_stats, statcast_data):
        """
        Compare actual stats vs expected stats (xBA, xSLG, xwOBA)
        
        Returns:
            Dict with signal or None
        """
        if not statcast_data:
            return None
        
        current_avg = current_stats.get('avg')
        current_slg = current_stats.get('slg')
        current_woba = current_stats.get('woba')
        
        xba = statcast_data.get('xba')
        xslg = statcast_data.get('xslg')
        xwoba = statcast_data.get('xwoba')
        
        if not all([current_woba, xwoba]):
            return None
        
        woba_diff = current_woba - xwoba
        
        # Actual wOBA significantly BELOW xwOBA = BUY
        if woba_diff < -0.020:
            return {
                'signal': 'BUY',
                'tier': 2,
                'metric': 'XWOBA_UNLUCKY',
                'explanation': f"wOBA {current_woba:.3f} vs xwOBA {xwoba:.3f} ({woba_diff:-.3f}) - Unlucky!",
                'confidence': 'MEDIUM'
            }
        
        # Actual wOBA significantly ABOVE xwOBA = SELL
        elif woba_diff > 0.020:
            return {
                'signal': 'SELL',
                'tier': 2,
                'metric': 'XWOBA_LUCKY',
                'explanation': f"wOBA {current_woba:.3f} vs xwOBA {xwoba:.3f} ({woba_diff:+.3f}) - Lucky!",
                'confidence': 'MEDIUM'
            }
        
        return None
    
    def analyze_player_season_with_statcast(self, player_id, season):
        """
        Enhanced regression analysis with Statcast data
        
        Returns:
            Dict with all signals (traditional + Statcast)
        """
        # Get traditional regression signals
        traditional_analysis = self.analyze_player_season(player_id, season)
        
        if not traditional_analysis:
            return None
        
        # Get Statcast data
        statcast_data = self.get_statcast_data(player_id, season)
        
        if not statcast_data:
            # No Statcast data available, return traditional analysis
            return traditional_analysis
        
        # Get career Statcast baseline
        statcast_baseline = self.get_career_statcast_baseline(player_id, season)
        
        # Get current season stats for comparison
        session = get_session()
        try:
            query = text("""
                SELECT babip, iso, avg, slg, woba
                FROM season_stats
                WHERE player_id = :player_id
                  AND season = :season
            """)
            result = session.execute(query, {'player_id': player_id, 'season': season})
            row = result.fetchone()
            
            current_stats = {
                'babip': float(row[0]) if row[0] else None,
                'iso': float(row[1]) if row[1] else None,
                'avg': float(row[2]) if row[2] else None,
                'slg': float(row[3]) if row[3] else None,
                'woba': float(row[4]) if row[4] else None,
            }
        finally:
            session.close()
        
        # Get career baseline
        career_baseline = self._get_player_career_baseline(player_id, season)
        
        if statcast_baseline:
            career_baseline.update(statcast_baseline)
        
        # Run Statcast-based detectors
        statcast_alerts = []
        
        # 1. Lucky vs Unlucky detection
        lucky_signal = self.detect_lucky_vs_unlucky(current_stats, statcast_data, career_baseline)
        if lucky_signal:
            statcast_alerts.append(lucky_signal)
        
        # 2. Power sustainability
        power_signal = self.detect_power_sustainability(current_stats, statcast_data, career_baseline)
        if power_signal:
            statcast_alerts.append(power_signal)
        
        # 3. Exit velocity decline
        ev_signal = self.detect_exit_velo_decline(statcast_data, statcast_baseline)
        if ev_signal:
            statcast_alerts.append(ev_signal)
        
        # 4. Expected stats divergence
        xstats_signal = self.detect_expected_stats_divergence(current_stats, statcast_data)
        if xstats_signal:
            statcast_alerts.append(xstats_signal)
        
        # Combine traditional + Statcast alerts
        all_alerts = traditional_analysis['alerts'] + statcast_alerts
        
        # Recalculate net score with Statcast signals
        tier1_buys = len([a for a in all_alerts if a['tier'] == 1 and a['signal'] == 'BUY'])
        tier1_sells = len([a for a in all_alerts if a['tier'] == 1 and a['signal'] == 'SELL'])
        tier2_buys = len([a for a in all_alerts if a['tier'] == 2 and a['signal'] == 'BUY'])
        tier2_sells = len([a for a in all_alerts if a['tier'] == 2 and a['signal'] == 'SELL'])
        
        net_score = (tier1_buys - tier1_sells) + (tier2_buys - tier2_sells) * 0.5
        
        return {
            'player_id': player_id,
            'season': season,
            'alerts': all_alerts,
            'net_score': net_score,
            'tier1_buys': tier1_buys,
            'tier1_sells': tier1_sells,
            'tier2_buys': tier2_buys,
            'tier2_sells': tier2_sells,
            'has_statcast': True,
            'statcast_data': statcast_data
        }
    
    def generate_statcast_report(self):
        """
        Generate enhanced regression report with Statcast insights
        """
        print("=" * 70)
        print("STATCAST-ENHANCED REGRESSION DETECTION")
        print("=" * 70)
        
        # Get all players with recent data
        session = get_session()
        
        try:
            query = text("""
                SELECT DISTINCT p.player_id, p.name, ss.season, ss.team
                FROM players p
                JOIN season_stats ss ON p.player_id = ss.player_id
                WHERE ss.season = 2025
                  AND ss.pa >= 100
                ORDER BY p.name
            """)
            
            players = session.execute(query).fetchall()
            
            print(f"\n📊 Analyzing {len(players)} players with 2025 data\n")
            
            # Analyze each player
            buy_candidates = []
            sell_candidates = []
            
            for player_id, name, season, team in players:
                analysis = self.analyze_player_season_with_statcast(player_id, season)
                
                if analysis and analysis['alerts']:
                    analysis['name'] = name
                    analysis['team'] = team
                    
                    if analysis['net_score'] >= 2:
                        buy_candidates.append(analysis)
                    elif analysis['net_score'] <= -2:
                        sell_candidates.append(analysis)
            
            # Sort by net score
            buy_candidates.sort(key=lambda x: x['net_score'], reverse=True)
            sell_candidates.sort(key=lambda x: x['net_score'])
            
            # Display results
            print("\n" + "=" * 70)
            print("🔴 STRONG SELL CANDIDATES")
            print("=" * 70)
            
            for analysis in sell_candidates[:10]:
                print(f"\n{analysis['name']} ({analysis['team']}) - Net: {analysis['net_score']:.1f}")
                
                for alert in analysis['alerts']:
                    if alert['signal'] == 'SELL':
                        tier_emoji = '🔴' if alert['tier'] == 1 else '🟡'
                        print(f"  {tier_emoji} TIER {alert['tier']} {alert['metric']}: {alert['explanation']}")
            
            print("\n" + "=" * 70)
            print("🟢 STRONG BUY CANDIDATES")
            print("=" * 70)
            
            for analysis in buy_candidates[:10]:
                print(f"\n{analysis['name']} ({analysis['team']}) - Net: {analysis['net_score']:+.1f}")
                
                for alert in analysis['alerts']:
                    if alert['signal'] == 'BUY':
                        tier_emoji = '🟢' if alert['tier'] == 1 else '🟡'
                        print(f"  {tier_emoji} TIER {alert['tier']} {alert['metric']}: {alert['explanation']}")
            
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"Strong Sell Candidates: {len(sell_candidates)}")
            print(f"Strong Buy Candidates: {len(buy_candidates)}")
            
        finally:
            session.close()


if __name__ == "__main__":
    detector = StatcastRegressionDetector()
    detector.generate_statcast_report()
