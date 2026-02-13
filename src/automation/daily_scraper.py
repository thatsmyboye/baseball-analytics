"""
Daily Automated Scraper

Runs daily to:
1. Update stats for all players in database
2. Detect new regression signals
3. Generate alerts
4. Log updates
"""
import sys
from pathlib import Path
from datetime import datetime
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.fangraphs import scrape_player_season_stats, parse_fangraphs_columns
from src.database.insert_data import load_player_to_database
from src.analytics.regression_detector import RegressionDetector
from src.utils.db_connection import get_session
from sqlalchemy import text

class DailyScraper:
    """
    Automated daily scraping and analysis
    """
    
    def __init__(self, log_file='daily_scraper.log'):
        self.log_file = log_file
        self.detector = RegressionDetector()
        self.updates = {
            'timestamp': datetime.now().isoformat(),
            'players_updated': [],
            'new_alerts': [],
            'errors': []
        }
    
    def log(self, message):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_all_tracked_players(self):
        """Get all players currently in database"""
        session = get_session()
        
        try:
            query = text("""
                SELECT p.player_id, p.name, p.fg_id
                FROM players p
                WHERE p.fg_id IS NOT NULL
                ORDER BY p.name
            """)
            
            result = session.execute(query).fetchall()
            return [(row[0], row[1], row[2]) for row in result]
        
        finally:
            session.close()
    
    def update_player_stats(self, player_name, fg_id, current_year=2025):
        """
        Update a single player's stats for current season
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Scrape current season
            data = scrape_player_season_stats(player_name, current_year, current_year)
            
            if data is None or data.empty:
                self.log(f"   ⚠️  No data for {player_name}")
                return False
            
            # Parse and load
            cleaned = parse_fangraphs_columns(data)
            load_player_to_database(player_name, fg_id, cleaned)
            
            self.log(f"   ✅ Updated {player_name}")
            return True
            
        except Exception as e:
            self.log(f"   ❌ Error updating {player_name}: {e}")
            self.updates['errors'].append({
                'player': player_name,
                'error': str(e)
            })
            return False
    
    def check_for_new_alerts(self, player_id, player_name, season=2025):
        """
        Check if player has any new regression alerts
        
        Returns:
            List of new alerts
        """
        analysis = self.detector.analyze_player_season(player_id, season)
        
        if not analysis or not analysis['alerts']:
            return []
        
        # Filter for significant alerts (Tier 1 and 2)
        significant_alerts = [
            alert for alert in analysis['alerts']
            if alert['tier'] <= 2
        ]
        
        return significant_alerts
    
    def run_daily_update(self, delay=2):
        """
        Run full daily update process
        """
        self.log("=" * 70)
        self.log("DAILY SCRAPER - Starting Update")
        self.log("=" * 70)
        
        # Get all tracked players
        players = self.get_all_tracked_players()
        self.log(f"\n📊 Found {len(players)} players to update")
        
        successful_updates = 0
        new_alerts_count = 0
        
        # Update each player
        for i, (player_id, player_name, fg_id) in enumerate(players, 1):
            self.log(f"\n[{i}/{len(players)}] Updating {player_name}...")
            
            # Update stats
            success = self.update_player_stats(player_name, fg_id)
            
            if success:
                successful_updates += 1
                self.updates['players_updated'].append(player_name)
                
                # Check for new alerts
                alerts = self.check_for_new_alerts(player_id, player_name)
                
                if alerts:
                    self.log(f"   🚨 {len(alerts)} new alert(s)")
                    new_alerts_count += len(alerts)
                    
                    self.updates['new_alerts'].append({
                        'player': player_name,
                        'alerts': [
                            {
                                'tier': a['tier'],
                                'metric': a['metric'],
                                'signal': a['signal'],
                                'message': a['message']
                            }
                            for a in alerts
                        ]
                    })
            
            # Rate limiting
            if i < len(players):
                import time
                time.sleep(delay)
        
        # Summary
        self.log("\n" + "=" * 70)
        self.log("DAILY SCRAPER - Summary")
        self.log("=" * 70)
        self.log(f"✅ Successfully updated: {successful_updates}/{len(players)}")
        self.log(f"🚨 New alerts detected: {new_alerts_count}")
        self.log(f"❌ Errors: {len(self.updates['errors'])}")
        
        # Save results
        self.save_results()
        
        return self.updates
    
    def save_results(self):
        """Save update results to JSON"""
        output_file = f"daily_update_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.updates, f, indent=2)
        
        self.log(f"\n📝 Results saved to {output_file}")


if __name__ == "__main__":
    print("=" * 70)
    print("DAILY AUTOMATED SCRAPER")
    print("=" * 70)
    
    scraper = DailyScraper()
    
    # Run update
    results = scraper.run_daily_update(delay=2)
    
    # Display new alerts if any
    if results['new_alerts']:
        print("\n\n🚨 NEW REGRESSION ALERTS:")
        print("=" * 70)
        
        for alert_group in results['new_alerts']:
            print(f"\n{alert_group['player']}:")
            for alert in alert_group['alerts']:
                tier_emoji = "🔴" if alert['tier'] == 1 else "🟡"
                print(f"   {tier_emoji} TIER {alert['tier']} {alert['metric']} - {alert['signal']}")
                print(f"      {alert['message']}")