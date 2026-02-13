"""
Batch Load Discovered Players with Progress Tracking

Loads players from discovery output with:
- Batch processing (load in groups of 50)
- Progress tracking and resume capability
- Rate limiting to avoid API blocks
- Error handling and retry logic
"""
import sys
from pathlib import Path
import json
import time
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.fangraphs import scrape_player_season_stats, parse_fangraphs_columns
from src.database.insert_data import load_player_to_database
import pandas as pd


class ProgressTracker:
    """
    Track progress of batch loading with resume capability
    """
    
    def __init__(self, progress_file='player_loading_progress.json'):
        self.progress_file = project_root / progress_file
        self.progress = self.load_progress()
    
    def load_progress(self):
        """Load existing progress if available"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {
            'completed': [],
            'failed': [],
            'remaining': [],
            'started_at': None,
            'last_updated': None
        }
    
    def save_progress(self):
        """Save current progress"""
        self.progress['last_updated'] = datetime.now().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def mark_completed(self, player_name, fg_id, seasons_loaded):
        """Mark player as successfully loaded"""
        self.progress['completed'].append({
            'name': player_name,
            'fg_id': fg_id,
            'seasons': seasons_loaded,
            'timestamp': datetime.now().isoformat()
        })
        self.save_progress()
    
    def mark_failed(self, player_name, fg_id, error):
        """Mark player as failed"""
        self.progress['failed'].append({
            'name': player_name,
            'fg_id': fg_id,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        self.save_progress()
    
    def is_completed(self, fg_id):
        """Check if player already loaded"""
        return any(p['fg_id'] == fg_id for p in self.progress['completed'])
    
    def get_stats(self):
        """Get progress statistics"""
        return {
            'completed': len(self.progress['completed']),
            'failed': len(self.progress['failed']),
            'remaining': len(self.progress['remaining'])
        }


class BatchPlayerLoader:
    """
    Load players in batches with progress tracking
    """
    
    def __init__(self, start_year=2015, end_year=2025, rate_limit_seconds=2):
        self.start_year = start_year
        self.end_year = end_year
        self.rate_limit = rate_limit_seconds
        self.tracker = ProgressTracker()
    
    def load_player_list(self, filename='new_verified_players.py'):
        """
        Load player list from discovery output
        
        Args:
            filename: Path to player list file
        
        Returns:
            List of (name, fg_id) tuples
        """
        filepath = project_root / filename
        
        if not filepath.exists():
            print(f"❌ File not found: {filename}")
            print(f"   Run discovery first: python src/scripts/discover_all_active_players.py")
            return []
        
        # Import the player list
        import importlib.util
        spec = importlib.util.spec_from_file_location("new_players", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        players = module.NEW_ACTIVE_PLAYERS
        print(f"📋 Loaded {len(players)} players from {filename}")
        
        return players
    
    def load_single_player(self, player_name, fg_id):
        """
        Load a single player's data
        
        Args:
            player_name: Player name
            fg_id: FanGraphs ID
        
        Returns:
            Tuple (success, seasons_loaded, error)
        """
        try:
            # Check if already loaded
            if self.tracker.is_completed(fg_id):
                return True, 0, "Already loaded"
            
            # Scrape stats using existing scraper
            # Temporarily inject player into ID map
            import src.scrapers.fangraphs as fg_module
            original_map = fg_module.get_fangraphs_playerid_map
            
            def temp_map():
                return {player_name: fg_id}
            
            fg_module.get_fangraphs_playerid_map = temp_map
            
            # Scrape data
            data = scrape_player_season_stats(player_name, self.start_year, self.end_year)
            
            # Restore original map
            fg_module.get_fangraphs_playerid_map = original_map
            
            if data is None or data.empty:
                return False, 0, "No data found"
            
            # Parse and load
            cleaned = parse_fangraphs_columns(data)
            load_player_to_database(player_name, fg_id, cleaned)
            
            return True, len(cleaned), None
            
        except Exception as e:
            return False, 0, str(e)
    
    def load_batch(self, players, batch_size=50, start_index=0):
        """
        Load players in batches
        
        Args:
            players: List of (name, fg_id) tuples
            batch_size: Number of players per batch
            start_index: Index to start from (for resume)
        
        Returns:
            Summary dict
        """
        total = len(players)
        
        if start_index > 0:
            print(f"▶️  Resuming from player {start_index + 1}/{total}")
        
        # Initialize tracking
        if not self.tracker.progress['started_at']:
            self.tracker.progress['started_at'] = datetime.now().isoformat()
            self.tracker.save_progress()
        
        successful = 0
        failed = 0
        skipped = 0
        
        for i in range(start_index, total):
            player_name, fg_id = players[i]
            player_num = i + 1
            
            print(f"\n[{player_num}/{total}] {player_name} (FG ID: {fg_id})")
            
            # Check if already completed
            if self.tracker.is_completed(fg_id):
                print(f"   ⏭️  Already loaded (skipping)")
                skipped += 1
                continue
            
            # Load player
            print(f"   Scraping {self.start_year}-{self.end_year}...", end=' ')
            
            success, seasons_loaded, error = self.load_single_player(player_name, fg_id)
            
            if success:
                print(f"✅ Loaded {seasons_loaded} seasons")
                self.tracker.mark_completed(player_name, fg_id, seasons_loaded)
                successful += 1
            else:
                print(f"❌ Failed: {error}")
                self.tracker.mark_failed(player_name, fg_id, error)
                failed += 1
            
            # Progress update every 10 players
            if player_num % 10 == 0:
                stats = self.tracker.get_stats()
                print(f"\n📊 Progress: {player_num}/{total} processed")
                print(f"   ✅ Success: {stats['completed']}")
                print(f"   ❌ Failed: {stats['failed']}")
                print(f"   Success rate: {stats['completed']/(stats['completed']+stats['failed'])*100:.1f}%")
            
            # Rate limiting
            if player_num < total:
                time.sleep(self.rate_limit)
        
        # Final summary
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'skipped': skipped
        }
    
    def run_batch_load(self, filename='new_verified_players.py', batch_size=50):
        """
        Run complete batch loading process
        
        Args:
            filename: Player list file
            batch_size: Number of players per batch (for display only)
        """
        print("=" * 70)
        print("BATCH PLAYER LOADING")
        print("=" * 70)
        
        # Load player list
        players = self.load_player_list(filename)
        
        if not players:
            return
        
        # Check for existing progress
        stats = self.tracker.get_stats()
        if stats['completed'] > 0:
            print(f"\n📊 Found existing progress:")
            print(f"   ✅ Completed: {stats['completed']}")
            print(f"   ❌ Failed: {stats['failed']}")
            print()
            
            response = input("Resume from where you left off? (yes/no): ").strip().lower()
            if response == 'yes' or response == 'y':
                start_index = stats['completed'] + stats['failed']
            else:
                response = input("Start fresh (clear progress)? (yes/no): ").strip().lower()
                if response == 'yes' or response == 'y':
                    self.tracker.progress = {
                        'completed': [],
                        'failed': [],
                        'remaining': [],
                        'started_at': None,
                        'last_updated': None
                    }
                    start_index = 0
                else:
                    print("Cancelled.")
                    return
        else:
            start_index = 0
        
        print(f"\n📋 Configuration:")
        print(f"   Total players: {len(players)}")
        print(f"   Year range: {self.start_year}-{self.end_year}")
        print(f"   Rate limit: {self.rate_limit}s between requests")
        print(f"   Starting at: Player {start_index + 1}")
        print()
        
        response = input("Proceed with batch loading? (yes/no): ").strip().lower()
        
        if response != 'yes' and response != 'y':
            print("Cancelled.")
            return
        
        # Run batch load
        print("\n" + "=" * 70)
        print("LOADING PLAYERS")
        print("=" * 70)
        
        start_time = time.time()
        
        summary = self.load_batch(players, batch_size, start_index)
        
        elapsed = time.time() - start_time
        
        # Final report
        print("\n" + "=" * 70)
        print("BATCH LOADING COMPLETE")
        print("=" * 70)
        
        print(f"\n📊 Summary:")
        print(f"   Total players: {summary['total']}")
        print(f"   ✅ Successfully loaded: {summary['successful']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⏭️  Skipped (already loaded): {summary['skipped']}")
        
        success_rate = summary['successful'] / (summary['successful'] + summary['failed']) * 100 if (summary['successful'] + summary['failed']) > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        print(f"\n⏱️  Time elapsed: {elapsed/60:.1f} minutes")
        print(f"   Average: {elapsed/summary['total']:.1f}s per player")
        
        # Failed players
        if self.tracker.progress['failed']:
            print(f"\n❌ Failed players ({len(self.tracker.progress['failed'])}):")
            for item in self.tracker.progress['failed'][-10:]:  # Show last 10
                print(f"   - {item['name']} (FG ID: {item['fg_id']}): {item['error']}")
            
            if len(self.tracker.progress['failed']) > 10:
                print(f"   ... and {len(self.tracker.progress['failed']) - 10} more")
            
            print(f"\n   Full error log: player_loading_progress.json")


if __name__ == "__main__":
    loader = BatchPlayerLoader(start_year=2015, end_year=2025, rate_limit_seconds=2)
    loader.run_batch_load()
