"""
Baseball Analytics System - Summary Report

Shows what we've built and current database stats
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.db_connection import get_session
from sqlalchemy import text

def generate_system_summary():
    """Generate comprehensive system summary"""
    session = get_session()
    
    try:
        report = []
        report.append("=" * 70)
        report.append("BASEBALL ANALYTICS SYSTEM - SUMMARY REPORT")
        report.append("=" * 70)
        
        # Database Stats
        report.append("\n📊 DATABASE STATISTICS")
        report.append("-" * 70)
        
        # Total players
        total_players = session.execute(text("SELECT COUNT(*) FROM players")).fetchone()[0]
        players_with_birthdate = session.execute(
            text("SELECT COUNT(*) FROM players WHERE birth_date IS NOT NULL")
        ).fetchone()[0]
        
        report.append(f"Total Players: {total_players}")
        report.append(f"   With birth dates: {players_with_birthdate}")
        report.append(f"   Without birth dates: {total_players - players_with_birthdate}")
        
        # Total player-seasons
        total_seasons = session.execute(text("SELECT COUNT(*) FROM season_stats")).fetchone()[0]
        report.append(f"\nTotal Player-Seasons: {total_seasons}")
        
        # Season coverage
        season_range = session.execute(
            text("SELECT MIN(season), MAX(season) FROM season_stats")
        ).fetchone()
        report.append(f"Season Range: {season_range[0]}-{season_range[1]}")
        
        # PA distribution
        pa_stats = session.execute(
            text("""
                SELECT 
                    MIN(pa) as min_pa,
                    AVG(pa) as avg_pa,
                    MAX(pa) as max_pa
                FROM season_stats
                WHERE pa > 0
            """)
        ).fetchone()
        report.append(f"\nPlate Appearances:")
        report.append(f"   Min: {pa_stats[0]:.0f}")
        report.append(f"   Average: {pa_stats[1]:.0f}")
        report.append(f"   Max: {pa_stats[2]:.0f}")
        
        # Top performers
        report.append("\n\n🏆 TOP 10 PERFORMERS (2025)")
        report.append("-" * 70)
        
        top_2025 = session.execute(
            text("""
                SELECT p.name, ss.wrc_plus, ss.pa, ss.hr
                FROM season_stats ss
                JOIN players p ON ss.player_id = p.player_id
                WHERE ss.season = 2025
                  AND ss.pa >= 200
                ORDER BY ss.wrc_plus DESC
                LIMIT 10
            """)
        ).fetchall()
        
        for i, (name, wrc, pa, hr) in enumerate(top_2025, 1):
            report.append(f"{i:2d}. {name:25s} wRC+: {wrc:3.0f}  PA: {pa:4.0f}  HR: {hr:2.0f}")
        
        # Analytics Capabilities
        report.append("\n\n🔬 ANALYTICS CAPABILITIES")
        report.append("-" * 70)
        
        capabilities = [
            "✅ Role Classification (9 categories)",
            "✅ Regression Detection (5 metrics: BABIP, K%, BB%, ISO, HR/FB%)",
            "✅ League Percentile Rankings",
            "✅ Historical Trend Tracking",
            "✅ Career Peak Detection",
            "✅ Aging Curve Analysis",
            "✅ Advanced Predictions with:",
            "   - Plate Discipline Scoring",
            "   - Power Sustainability Assessment",
            "   - Contact Quality Evaluation",
            "   - Skill Change Detection",
            "   - Multi-Component Projections",
            "✅ Comprehensive Player Reports",
            "✅ Automated Daily Updates",
            "✅ Alert Digest Generation"
        ]
        
        for cap in capabilities:
            report.append(cap)
        
        # Data Sources
        report.append("\n\n📡 DATA SOURCES")
        report.append("-" * 70)
        report.append("Primary: FanGraphs API")
        report.append("   - Standard batting stats")
        report.append("   - Advanced metrics (wRC+, wOBA, BABIP)")
        report.append("   - Plate discipline (K%, BB%)")
        report.append("   - Batted ball data (ISO, HR/FB%)")
        
        # System Files
        report.append("\n\n📁 SYSTEM COMPONENTS")
        report.append("-" * 70)
        
        components = {
            "Database": [
                "src/database/schema.sql",
                "src/utils/db_connection.py",
                "src/database/insert_data.py"
            ],
            "Scrapers": [
                "src/scrapers/fangraphs.py",
                "src/scrapers/batch_scraper.py",
                "src/data/player_id_resolver.py"
            ],
            "Analytics": [
                "src/analytics/role_classifier.py",
                "src/analytics/regression_detector.py",
                "src/analytics/league_baselines.py",
                "src/analytics/trend_tracker.py",
                "src/analytics/predictive_model.py",
                "src/analytics/player_report.py"
            ],
            "Automation": [
                "src/automation/daily_scraper.py",
                "src/automation/alert_digest.py"
            ]
        }
        
        for category, files in components.items():
            report.append(f"\n{category}:")
            for f in files:
                report.append(f"   - {f}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    finally:
        session.close()

if __name__ == "__main__":
    summary = generate_system_summary()
    print(summary)
    
    # Save to file
    with open("SYSTEM_SUMMARY.txt", "w") as f:
        f.write(summary)
    
    print("\n📝 Summary saved to SYSTEM_SUMMARY.txt")