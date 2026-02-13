"""
Expand player database with verified players from Razzball data
"""
import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.player_id_resolver import get_active_batters
from src.scrapers.fangraphs import scrape_player_season_stats, parse_fangraphs_columns
from src.database.insert_data import load_player_to_database
from src.utils.db_connection import get_session
from sqlalchemy import text

class PlayerDatabaseExpander:
    """
    Intelligently expand player database
    """
    
    def __init__(self):
        self.session = get_session()
    
    def get_existing_players(self):
        """Get list of players already in database"""
        result = self.session.execute(
            text("SELECT name, fg_id FROM players")
        ).fetchall()
        
        existing = {}
        for name, fg_id in result:
            if fg_id:
                existing[fg_id] = name
        
        return existing
    
    def test_player_id(self, player_name, fg_id, test_year=2024):
        """
        Test if a FanGraphs ID actually works
        
        Returns:
            True if valid, False otherwise
        """
        try:
            data = scrape_player_season_stats(player_name, test_year, test_year)
            
            if data is not None and not data.empty:
                return True
            return False
            
        except Exception:
            return False
    
    def add_players_batch(self, player_list, start_year=2015, end_year=2025, 
                         test_first=True, delay=2):
        """
        Add multiple players with optional ID verification
        
        Args:
            player_list: List of (name, fg_id) tuples
            start_year: First season to scrape
            end_year: Last season to scrape
            test_first: Test ID before full scrape
            delay: Delay between requests
        
        Returns:
            Dict with results
        """
        results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'total': len(player_list)
        }
        
        print(f"📊 Processing {len(player_list)} players...")
        print(f"   Test IDs first: {test_first}")
        print(f"   Year range: {start_year}-{end_year}")
        print(f"   Delay: {delay}s\n")
        
        for i, (player_name, fg_id) in enumerate(player_list, 1):
            print(f"[{i}/{len(player_list)}] {player_name} (FG ID: {fg_id})...")
            
            # Test ID first if requested
            if test_first:
                print(f"   Testing ID...")
                if not self.test_player_id(player_name, fg_id):
                    print(f"   ⚠️  ID doesn't work, skipping")
                    results['skipped'].append((player_name, fg_id, "Invalid ID"))
                    continue
            
            try:
                # Scrape full career
                print(f"   Scraping {start_year}-{end_year}...")
                data = scrape_player_season_stats(player_name, start_year, end_year)
                
                if data is None or data.empty:
                    print(f"   ⚠️  No data found")
                    results['failed'].append((player_name, fg_id, "No data"))
                    continue
                
                # Parse and load
                cleaned = parse_fangraphs_columns(data)
                load_player_to_database(player_name, fg_id, cleaned)
                
                print(f"   ✅ Success ({len(cleaned)} seasons)")
                results['successful'].append((player_name, fg_id))
                
                # Rate limiting
                if i < len(player_list):
                    time.sleep(delay)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results['failed'].append((player_name, fg_id, str(e)))
        
        return results
    
    def expand_to_target_count(self, target_count=100, test_first=True):
        """
        Expand database to target number of players
        
        Selects new players from Razzball data
        """
        # Get existing players
        existing = self.get_existing_players()
        current_count = len(existing)
        
        print(f"📊 Current player count: {current_count}")
        print(f"   Target count: {target_count}")
        
        if current_count >= target_count:
            print(f"✅ Already at or above target!")
            return
        
        needed = target_count - current_count
        print(f"   Need to add: {needed} players\n")
        
        # Get all active batters
        all_batters = get_active_batters()
        
        # Filter out existing
        new_players = [
            (name, fg_id) for name, fg_id in all_batters
            if fg_id not in existing
        ]
        
        print(f"📋 Found {len(new_players)} new players available")
        print(f"   Selecting first {needed}...\n")
        
        # Take the needed amount
        to_add = new_players[:needed]
        
        # Add them
        results = self.add_players_batch(
            to_add,
            start_year=2015,
            end_year=2025,
            test_first=test_first,
            delay=2
        )
        
        # Summary
        print("\n" + "=" * 70)
        print("EXPANSION SUMMARY")
        print("=" * 70)
        print(f"Attempted: {results['total']}")
        print(f"✅ Successful: {len(results['successful'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"⏭️  Skipped (bad IDs): {len(results['skipped'])}")
        
        new_count = current_count + len(results['successful'])
        print(f"\n📊 New player count: {new_count}")
        print(f"   Progress: {new_count}/{target_count} ({new_count/target_count*100:.1f}%)")
        
        if results['failed']:
            print(f"\n⚠️  Top failures:")
            for name, fg_id, error in results['failed'][:5]:
                print(f"   - {name}: {error}")
        
        return results
    
    def add_specific_players(self, player_names):
        """
        Add specific players by name
        
        Args:
            player_names: List of player names to add
        """
        # Get all active batters
        all_batters = get_active_batters()
        batter_dict = {name: fg_id for name, fg_id in all_batters}
        
        # Find matching players
        to_add = []
        not_found = []
        
        for name in player_names:
            if name in batter_dict:
                to_add.append((name, batter_dict[name]))
            else:
                not_found.append(name)
        
        if not_found:
            print(f"⚠️  Could not find {len(not_found)} players:")
            for name in not_found:
                print(f"   - {name}")
            print()
        
        if to_add:
            print(f"📊 Adding {len(to_add)} players...\n")
            return self.add_players_batch(to_add, test_first=True, delay=2)
        
        return None
    
    def close(self):
        """Close database session"""
        self.session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("PLAYER DATABASE EXPANDER")
    print("=" * 70)
    print()
    
    expander = PlayerDatabaseExpander()
    
    # Show options
    print("Options:")
    print("  1. Expand to specific player count (e.g., 100, 200 players)")
    print("  2. Add specific players by name")
    print("  3. Add top N players from Razzball list")
    print()
    
    choice = input("Select option (1-3): ")
    
    try:
        if choice == "1":
            target = int(input("Target player count: "))
            expander.expand_to_target_count(target_count=target, test_first=True)
        
        elif choice == "2":
            print("\nEnter player names (one per line, empty line to finish):")
            names = []
            while True:
                name = input("  ")
                if not name:
                    break
                names.append(name)
            
            if names:
                expander.add_specific_players(names)
        
        elif choice == "3":
            n = int(input("How many top players to add: "))
            
            all_batters = get_active_batters()
            existing = expander.get_existing_players()
            
            new_players = [
                (name, fg_id) for name, fg_id in all_batters
                if fg_id not in existing
            ][:n]
            
            print(f"\nAdding {len(new_players)} players...\n")
            expander.add_players_batch(new_players, test_first=True, delay=2)
    
    finally:
        expander.close()