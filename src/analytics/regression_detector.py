"""
Regression Detection Engine - Enhanced Version

Detects regression candidates using multiple metrics:
- BABIP (luck-based)
- K% and BB% (plate discipline)
- ISO and HR/FB% (power sustainability)
- Multi-metric analysis
"""
import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db_connection import get_session

class RegressionDetector:
    """
    Detect players due for positive or negative regression
    """
    
    # BABIP thresholds
    TIER_1_BABIP_DELTA = 0.050
    TIER_2_BABIP_DELTA = 0.030
    TIER_3_BABIP_DELTA = 0.015
    
    # K% thresholds (percentage points)
    TIER_1_K_DELTA = 5.0
    TIER_2_K_DELTA = 3.0
    TIER_3_K_DELTA = 1.5
    
    # BB% thresholds (percentage points)
    TIER_1_BB_DELTA = 4.0
    TIER_2_BB_DELTA = 2.5
    TIER_3_BB_DELTA = 1.5
    
    # ISO thresholds
    TIER_1_ISO_DELTA = 0.060
    TIER_2_ISO_DELTA = 0.040
    TIER_3_ISO_DELTA = 0.025
    
    # HR/FB% thresholds
    TIER_1_HRFB_DELTA = 8.0
    TIER_2_HRFB_DELTA = 5.0
    TIER_3_HRFB_DELTA = 3.0
    
    def __init__(self):
        self.league_averages = self._calculate_league_averages()
    
    def _calculate_league_averages(self):
        """Calculate league average metrics by season"""
        session = get_session()
        
        try:
            query = """
                SELECT 
                    season,
                    AVG(babip) as avg_babip,
                    AVG(bb_pct) as avg_bb_pct,
                    AVG(k_pct) as avg_k_pct,
                    AVG(iso) as avg_iso,
                    AVG(hr_fb_pct) as avg_hr_fb_pct,
                    COUNT(*) as player_count
                FROM season_stats
                WHERE babip IS NOT NULL 
                  AND pa >= 100
                GROUP BY season
                ORDER BY season
            """
            
            df = pd.read_sql(query, session.bind)
            return df
        
        finally:
            session.close()
    
    def _get_player_career_baseline(self, player_id, current_season):
        """Get player's career baseline stats (excluding current season)"""
        session = get_session()
        
        try:
            query = """
                SELECT 
                    AVG(babip) as career_babip,
                    AVG(bb_pct) as career_bb_pct,
                    AVG(k_pct) as career_k_pct,
                    AVG(iso) as career_iso,
                    AVG(hr_fb_pct) as career_hr_fb_pct,
                    SUM(pa) as total_pa,
                    COUNT(*) as seasons
                FROM season_stats
                WHERE player_id = :player_id
                  AND season < :season
                  AND pa >= 50
            """
            
            result = session.execute(
                text(query),
                {'player_id': player_id, 'season': current_season}
            ).fetchone()
            
            if result and result[5] and result[5] >= 200:  # Need 200+ career PA
                return {
                    'career_babip': result[0],
                    'career_bb_pct': result[1],
                    'career_k_pct': result[2],
                    'career_iso': result[3],
                    'career_hr_fb_pct': result[4],
                    'total_pa': result[5],
                    'seasons': result[6]
                }
            
            return None
        
        finally:
            session.close()
    
    def _determine_tier(self, delta, tier1_threshold, tier2_threshold, tier3_threshold):
        """Helper to determine alert tier based on delta"""
        abs_delta = abs(delta)
        if abs_delta >= tier1_threshold:
            return 1
        elif abs_delta >= tier2_threshold:
            return 2
        elif abs_delta >= tier3_threshold:
            return 3
        return None
    
    def detect_babip_regression(self, current_babip, career_babip):
        """Detect BABIP-based regression"""
        if current_babip is None or career_babip is None:
            return None
        
        delta = current_babip - career_babip
        tier = self._determine_tier(delta, self.TIER_1_BABIP_DELTA, 
                                    self.TIER_2_BABIP_DELTA, self.TIER_3_BABIP_DELTA)
        
        if tier is None:
            return None
        
        direction = 'negative' if delta > 0 else 'positive'
        signal = 'SELL' if delta > 0 else 'BUY'
        
        return {
            'metric': 'BABIP',
            'tier': tier,
            'direction': direction,
            'signal': signal,
            'current': current_babip,
            'expected': career_babip,
            'delta': delta,
            'message': f"BABIP {current_babip:.3f} is {delta:+.3f} from career {career_babip:.3f}"
        }
    
    def detect_k_rate_regression(self, current_k_pct, career_k_pct):
        """Detect K% regression (lower is better)"""
        if current_k_pct is None or career_k_pct is None:
            return None
        
        delta = current_k_pct - career_k_pct
        tier = self._determine_tier(delta, self.TIER_1_K_DELTA, 
                                    self.TIER_2_K_DELTA, self.TIER_3_K_DELTA)
        
        if tier is None:
            return None
        
        # Higher K% is bad (negative), lower K% is good (positive)
        direction = 'negative' if delta > 0 else 'positive'
        signal = 'SELL' if delta > 0 else 'BUY'
        
        return {
            'metric': 'K%',
            'tier': tier,
            'direction': direction,
            'signal': signal,
            'current': current_k_pct,
            'expected': career_k_pct,
            'delta': delta,
            'message': f"K% {current_k_pct:.1f}% is {delta:+.1f}pp from career {career_k_pct:.1f}%"
        }
    
    def detect_bb_rate_regression(self, current_bb_pct, career_bb_pct):
        """Detect BB% regression (higher is better)"""
        if current_bb_pct is None or career_bb_pct is None:
            return None
        
        delta = current_bb_pct - career_bb_pct
        tier = self._determine_tier(delta, self.TIER_1_BB_DELTA, 
                                    self.TIER_2_BB_DELTA, self.TIER_3_BB_DELTA)
        
        if tier is None:
            return None
        
        # Higher BB% is good (positive), lower BB% is bad (negative)
        direction = 'positive' if delta > 0 else 'negative'
        signal = 'BUY' if delta > 0 else 'SELL'
        
        return {
            'metric': 'BB%',
            'tier': tier,
            'direction': direction,
            'signal': signal,
            'current': current_bb_pct,
            'expected': career_bb_pct,
            'delta': delta,
            'message': f"BB% {current_bb_pct:.1f}% is {delta:+.1f}pp from career {career_bb_pct:.1f}%"
        }
    
    def detect_iso_regression(self, current_iso, career_iso):
        """Detect ISO regression (power)"""
        if current_iso is None or career_iso is None:
            return None
        
        delta = current_iso - career_iso
        tier = self._determine_tier(delta, self.TIER_1_ISO_DELTA, 
                                    self.TIER_2_ISO_DELTA, self.TIER_3_ISO_DELTA)
        
        if tier is None:
            return None
        
        direction = 'positive' if delta > 0 else 'negative'
        signal = 'BUY' if delta > 0 else 'SELL'
        
        return {
            'metric': 'ISO',
            'tier': tier,
            'direction': direction,
            'signal': signal,
            'current': current_iso,
            'expected': career_iso,
            'delta': delta,
            'message': f"ISO {current_iso:.3f} is {delta:+.3f} from career {career_iso:.3f}"
        }
    
    def detect_hr_fb_regression(self, current_hr_fb, career_hr_fb):
        """Detect HR/FB% regression (power sustainability)"""
        if current_hr_fb is None or career_hr_fb is None:
            return None
        
        delta = current_hr_fb - career_hr_fb
        tier = self._determine_tier(delta, self.TIER_1_HRFB_DELTA, 
                                    self.TIER_2_HRFB_DELTA, self.TIER_3_HRFB_DELTA)
        
        if tier is None:
            return None
        
        direction = 'negative' if delta > 0 else 'positive'
        signal = 'SELL' if delta > 0 else 'BUY'
        
        return {
            'metric': 'HR/FB%',
            'tier': tier,
            'direction': direction,
            'signal': signal,
            'current': current_hr_fb,
            'expected': career_hr_fb,
            'delta': delta,
            'message': f"HR/FB {current_hr_fb:.1f}% is {delta:+.1f}pp from career {career_hr_fb:.1f}%"
        }
    
    def analyze_player_season(self, player_id, season):
        """
        Comprehensive regression analysis for a player-season
        
        Returns:
            dict with all alerts and metrics
        """
        session = get_session()
        
        try:
            # Get current season stats
            query = """
                SELECT 
                    p.name,
                    ss.team,
                    ss.pa,
                    ss.games,
                    ss.avg,
                    ss.obp,
                    ss.slg,
                    ss.woba,
                    ss.wrc_plus,
                    ss.babip,
                    ss.bb_pct,
                    ss.k_pct,
                    ss.iso,
                    ss.hr_fb_pct
                FROM season_stats ss
                JOIN players p ON ss.player_id = p.player_id
                WHERE ss.player_id = :player_id 
                  AND ss.season = :season
            """
            
            result = session.execute(
                text(query),
                {'player_id': player_id, 'season': season}
            ).fetchone()
            
            if not result:
                return None
            
            # Get career baseline
            career_baseline = self._get_player_career_baseline(player_id, season)
            
            if not career_baseline:
                return None  # Need career history for regression analysis
            
            # Get league average for this season
            league_avg = self.league_averages[
                self.league_averages['season'] == season
            ].iloc[0] if len(self.league_averages[self.league_averages['season'] == season]) > 0 else None
            
            # Run all regression checks
            all_alerts = []
            
            # BABIP regression
            babip_alert = self.detect_babip_regression(result[9], career_baseline['career_babip'])
            if babip_alert:
                all_alerts.append(babip_alert)
            
            # K% regression
            k_alert = self.detect_k_rate_regression(result[11], career_baseline['career_k_pct'])
            if k_alert:
                all_alerts.append(k_alert)
            
            # BB% regression
            bb_alert = self.detect_bb_rate_regression(result[10], career_baseline['career_bb_pct'])
            if bb_alert:
                all_alerts.append(bb_alert)
            
            # ISO regression
            iso_alert = self.detect_iso_regression(result[12], career_baseline['career_iso'])
            if iso_alert:
                all_alerts.append(iso_alert)
            
            # HR/FB% regression
            hrfb_alert = self.detect_hr_fb_regression(result[13], career_baseline['career_hr_fb_pct'])
            if hrfb_alert:
                all_alerts.append(hrfb_alert)
            
            # Calculate composite score
            buy_signals = len([a for a in all_alerts if a['signal'] == 'BUY'])
            sell_signals = len([a for a in all_alerts if a['signal'] == 'SELL'])
            
            return {
                'player_id': player_id,
                'name': result[0],
                'season': season,
                'team': result[1],
                'pa': result[2],
                'games': result[3],
                'current_stats': {
                    'avg': result[4],
                    'obp': result[5],
                    'slg': result[6],
                    'woba': result[7],
                    'wrc_plus': result[8],
                    'babip': result[9],
                    'bb_pct': result[10],
                    'k_pct': result[11],
                    'iso': result[12],
                    'hr_fb_pct': result[13],
                },
                'career_baseline': career_baseline,
                'alerts': all_alerts,
                'alert_count': len(all_alerts),
                'max_tier': min([a['tier'] for a in all_alerts]) if all_alerts else None,
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'net_signal': buy_signals - sell_signals,  # Positive = more BUY, Negative = more SELL
            }
        
        finally:
            session.close()
    
    def scan_all_current_season(self, season=2025, min_pa=100):
        """
        Scan all players in a given season for regression candidates
        """
        session = get_session()
        
        try:
            query = """
                SELECT DISTINCT player_id
                FROM season_stats
                WHERE season = :season
                  AND pa >= :min_pa
            """
            
            result = session.execute(
                text(query),
                {'season': season, 'min_pa': min_pa}
            ).fetchall()
            
            player_ids = [row[0] for row in result]
            
            print(f"🔍 Scanning {len(player_ids)} players from {season} season...")
            
            results = []
            for player_id in player_ids:
                analysis = self.analyze_player_season(player_id, season)
                if analysis and analysis['alert_count'] > 0:
                    results.append(analysis)
            
            return results
        
        finally:
            session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Regression Detection Engine")
    print("=" * 60)
    
    detector = RegressionDetector()
    
    # Test with Harrison Bader 2024
    print("\n🔍 Testing with Harrison Bader 2024...")
    
    session = get_session()
    bader_id = session.execute(
        text("SELECT player_id FROM players WHERE name = 'Harrison Bader'")
    ).fetchone()[0]
    session.close()
    
    analysis = detector.analyze_player_season(bader_id, 2024)
    
    if analysis:
        print(f"\n📊 {analysis['name']} - {analysis['season']} {analysis['team']}")
        print(f"   Games: {analysis['games']} | PA: {analysis['pa']}")
        avg_display = int(analysis['current_stats']['avg']*1000)
        obp_display = int(analysis['current_stats']['obp']*1000)
        slg_display = int(analysis['current_stats']['slg']*1000)
        print(f"   Slash: .{avg_display}/{obp_display}/{slg_display}")
        print(f"   wRC+: {analysis['current_stats']['wrc_plus']}")
        
        print(f"\n📈 Key Metrics vs Career:")
        print(f"   BABIP: {analysis['current_stats']['babip']:.3f} (career: {analysis['career_baseline']['career_babip']:.3f})")
        print(f"   K%: {analysis['current_stats']['k_pct']:.1f}% (career: {analysis['career_baseline']['career_k_pct']:.1f}%)")
        print(f"   BB%: {analysis['current_stats']['bb_pct']:.1f}% (career: {analysis['career_baseline']['career_bb_pct']:.1f}%)")
        print(f"   ISO: {analysis['current_stats']['iso']:.3f} (career: {analysis['career_baseline']['career_iso']:.3f})")
        
        alert_count = len(analysis['alerts'])
        if analysis['alerts']:
            print(f"\n🚨 REGRESSION ALERTS ({alert_count}):")
            print(f"   Net Signal: {analysis['net_signal']} ({analysis['buy_signals']} BUY, {analysis['sell_signals']} SELL)")
            
            for alert in sorted(analysis['alerts'], key=lambda x: x['tier']):
                tier_emoji = "🔴" if alert['tier'] == 1 else "🟡" if alert['tier'] == 2 else "🟢"
                print(f"   {tier_emoji} TIER {alert['tier']} {alert['metric']:8s} - {alert['signal']:4s}: {alert['message']}")
        else:
            print("\n✅ No regression alerts")
    
    # Scan 2025 season
    print("\n\n🔄 Scanning 2025 season for regression candidates...")
    candidates = detector.scan_all_current_season(season=2025, min_pa=100)
    
    candidate_count = len(candidates)
    print(f"\n✅ Found {candidate_count} players with regression signals")
    
    # Sort by alert strength
    tier1 = [c for c in candidates if c['max_tier'] == 1]
    strong_buy = [c for c in tier1 if c['net_signal'] >= 2]  # Multiple BUY signals
    strong_sell = [c for c in tier1 if c['net_signal'] <= -2]  # Multiple SELL signals
    
    if strong_buy:
        print(f"\n🟢 STRONG BUY CANDIDATES ({len(strong_buy)}):")
        for candidate in sorted(strong_buy, key=lambda x: x['net_signal'], reverse=True)[:5]:
            print(f"\n   {candidate['name']} ({candidate['team']}) - Net: +{candidate['net_signal']}")
            for alert in sorted(candidate['alerts'], key=lambda x: x['tier'])[:3]:
                if alert['signal'] == 'BUY':
                    tier_emoji = "🔴" if alert['tier'] == 1 else "🟡" if alert['tier'] == 2 else "🟢"
                    print(f"      {tier_emoji} {alert['metric']}: {alert['message']}")
    
    if strong_sell:
        print(f"\n🔴 STRONG SELL CANDIDATES ({len(strong_sell)}):")
        for candidate in sorted(strong_sell, key=lambda x: x['net_signal'])[:5]:
            print(f"\n   {candidate['name']} ({candidate['team']}) - Net: {candidate['net_signal']}")
            for alert in sorted(candidate['alerts'], key=lambda x: x['tier'])[:3]:
                if alert['signal'] == 'SELL':
                    tier_emoji = "🔴" if alert['tier'] == 1 else "🟡" if alert['tier'] == 2 else "🟢"
                    print(f"      {tier_emoji} {alert['metric']}: {alert['message']}")