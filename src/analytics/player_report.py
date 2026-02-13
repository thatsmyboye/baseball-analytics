"""
Comprehensive Player Analytics Report

Combines:
- Role classification
- Regression detection  
- League percentile rankings
- Career trends
"""
import pandas as pd
from sqlalchemy import text
from src.utils.db_connection import get_session
from src.analytics.role_classifier import RoleClassifier
from src.analytics.regression_detector import RegressionDetector
from src.analytics.league_baselines import LeagueBaselines

class PlayerReport:
    """
    Generate comprehensive analytics reports for players
    """
    
    def __init__(self):
        self.classifier = RoleClassifier()
        self.detector = RegressionDetector()
        self.baselines = LeagueBaselines()
    
    def generate_player_report(self, player_name, season=2024):
        """
        Generate a comprehensive report for a player's season
        
        Returns:
            Formatted report string
        """
        session = get_session()
        
        try:
            # Get player ID
            result = session.execute(
                text("SELECT player_id FROM players WHERE name = :name"),
                {'name': player_name}
            ).fetchone()
            
            if not result:
                return f"Player '{player_name}' not found in database"
            
            player_id = result[0]
            
            # Get season stats
            stats_result = session.execute(
                text("""
                    SELECT 
                        team, games, pa, ab, hits, hr,
                        avg, obp, slg, woba, wrc_plus, babip,
                        bb_pct, k_pct, iso, hr_fb_pct
                    FROM season_stats
                    WHERE player_id = :player_id AND season = :season
                """),
                {'player_id': player_id, 'season': season}
            ).fetchone()
            
            if not stats_result:
                return f"No {season} season data found for {player_name}"
            
            # Build report
            report = []
            report.append("=" * 70)
            report.append(f"PLAYER ANALYTICS REPORT: {player_name} ({season})")
            report.append("=" * 70)
            
            # Basic stats
            report.append("\n📊 SEASON STATISTICS")
            report.append(f"   Team: {stats_result[0]}")
            report.append(f"   Games: {stats_result[1]} | PA: {stats_result[2]} | AB: {stats_result[3]}")
            report.append(f"   Hits: {stats_result[4]} | HR: {stats_result[5]}")
            
            avg = stats_result[6] * 1000 if stats_result[6] else 0
            obp = stats_result[7] * 1000 if stats_result[7] else 0
            slg = stats_result[8] * 1000 if stats_result[8] else 0
            report.append(f"   Slash: .{int(avg)}/{int(obp)}/{int(slg)}")
            report.append(f"   wOBA: {stats_result[9]:.3f} | wRC+: {stats_result[10]}")
            
            # Advanced metrics
            report.append("\n📈 ADVANCED METRICS")
            report.append(f"   BABIP: {stats_result[11]:.3f}")
            report.append(f"   BB%: {stats_result[12]*100:.1f}% | K%: {stats_result[13]*100:.1f}%")
            report.append(f"   ISO: {stats_result[14]:.3f}")
            if stats_result[15]:
                report.append(f"   HR/FB: {stats_result[15]:.1f}%")
            
            # Role classification
            role_result = self.classifier.classify_season(
                player_id, season, stats_result[1], stats_result[2]
            )
            report.append("\n🎯 ROLE CLASSIFICATION")
            report.append(f"   Role: {role_result['role']}")
            report.append(f"   Confidence: {role_result['confidence']*100:.0f}%")
            report.append(f"   PA per Team Game: {role_result['pa_per_team_game']:.2f}")
            report.append(f"   Games Played: {role_result['games_played_pct']*100:.1f}%")
            
            # League percentiles
            player_stats = {
                'wrc_plus': stats_result[10],
                'babip': stats_result[11],
                'bb_pct': stats_result[12],
                'k_pct': stats_result[13],
                'iso': stats_result[14],
                'avg': stats_result[6],
                'obp': stats_result[7],
                'slg': stats_result[8]
            }
            
            percentiles = self.baselines.compare_player_to_league(
                player_stats, season=season, min_pa=100
            )
            
            report.append("\n📊 LEAGUE PERCENTILE RANKINGS")
            for metric, data in sorted(percentiles.items(), 
                                      key=lambda x: x[1]['percentile'], 
                                      reverse=True):
                val = data['value']
                pct = data['percentile']
                tier = data['tier']
                
                # Format value
                if metric in ['AVG', 'OBP', 'SLG', 'BABIP', 'ISO']:
                    val_str = f"{val:.3f}"
                elif metric in ['BB%', 'K%']:
                    val_str = f"{val*100:.1f}%"
                else:
                    val_str = f"{val:.0f}"
                
                report.append(f"   {metric:8s}: {val_str:>7s} - {pct:3d}th %ile ({tier})")
            
            # Regression analysis
            regression = self.detector.analyze_player_season(player_id, season)
            
            if regression and regression['alerts']:
                report.append("\n🚨 REGRESSION ALERTS")
                report.append(f"   Net Signal: {regression['net_signal']} " +
                            f"({regression['buy_signals']} BUY, {regression['sell_signals']} SELL)")
                
                for alert in sorted(regression['alerts'], key=lambda x: x['tier']):
                    tier_emoji = "🔴" if alert['tier'] == 1 else "🟡" if alert['tier'] == 2 else "🟢"
                    report.append(f"   {tier_emoji} TIER {alert['tier']} {alert['metric']:8s} - " +
                                f"{alert['signal']:4s}: {alert['message']}")
            else:
                report.append("\n✅ NO REGRESSION ALERTS")
                report.append("   Performance aligns with career baseline")
            
            # Career context
            career_result = session.execute(
                text("""
                    SELECT 
                        COUNT(*) as seasons,
                        SUM(pa) as career_pa,
                        AVG(wrc_plus) as avg_wrc_plus,
                        MIN(season) as debut,
                        MAX(season) as last_season
                    FROM season_stats
                    WHERE player_id = :player_id
                      AND season <= :season
                """),
                {'player_id': player_id, 'season': season}
            ).fetchone()
            
            report.append("\n📜 CAREER CONTEXT")
            report.append(f"   MLB Seasons: {career_result[0]}")
            report.append(f"   Career PA: {career_result[1]}")
            report.append(f"   Career Avg wRC+: {career_result[2]:.0f}")
            report.append(f"   Debut: {career_result[3]} | Through: {career_result[4]}")
            
            report.append("\n" + "=" * 70)
            
            return "\n".join(report)
        
        finally:
            session.close()
    
    def generate_top_performers_report(self, season=2025, min_pa=200, top_n=10):
        """
        Generate report of top performers by wRC+
        """
        session = get_session()
        
        try:
            query = text("""
                SELECT 
                    p.name, ss.team, ss.wrc_plus, ss.pa,
                    ss.avg, ss.obp, ss.slg, ss.hr
                FROM season_stats ss
                JOIN players p ON ss.player_id = p.player_id
                WHERE ss.season = :season
                  AND ss.pa >= :min_pa
                ORDER BY ss.wrc_plus DESC
                LIMIT :limit
            """)
            
            results = session.execute(
                query,
                {'season': season, 'min_pa': min_pa, 'limit': top_n}
            ).fetchall()
            
            report = []
            report.append("=" * 70)
            report.append(f"TOP {top_n} PERFORMERS - {season} SEASON (min {min_pa} PA)")
            report.append("=" * 70)
            report.append(f"\n{'Rank':<6}{'Player':<20}{'Team':<6}{'wRC+':<8}{'PA':<8}{'AVG/OBP/SLG':<20}{'HR':<6}")
            report.append("-" * 70)
            
            for i, row in enumerate(results, 1):
                name = row[0][:18]
                team = row[1]
                wrc_plus = row[2]
                pa = row[3]
                slash = f".{int(row[4]*1000)}/{int(row[5]*1000)}/{int(row[6]*1000)}"
                hr = row[7]
                
                report.append(f"{i:<6}{name:<20}{team:<6}{wrc_plus:<8.0f}{pa:<8}{slash:<20}{hr:<6}")
            
            report.append("=" * 70)
            
            return "\n".join(report)
        
        finally:
            session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("PLAYER ANALYTICS REPORT GENERATOR")
    print("=" * 70)
    
    reporter = PlayerReport()
    
    # Generate Harrison Bader report
    print("\n📋 Generating report for Harrison Bader 2024...\n")
    report = reporter.generate_player_report("Harrison Bader", 2024)
    print(report)
    
    # Generate top performers
    print("\n\n📋 Generating top performers report for 2025...\n")
    top_report = reporter.generate_top_performers_report(season=2025, min_pa=100, top_n=15)
    print(top_report)