"""
Discover All Active MLB Players using pybaseball

Automatically finds all qualified players from recent seasons and looks up their IDs.
This expands the database from 53 to 400-600+ active players.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pybaseball import batting_stats, cache
import pandas as pd
from src.integrations.pybaseball_bridge import PybaseballBridge
from src.utils.db_connection import get_session
from sqlalchemy import text

cache.enable()


class ActivePlayerDiscovery:
    """
    Discover all active MLB players using batting leaderboards
    """
    
    def __init__(self):
        self.bridge = PybaseballBridge()
    
    def get_existing_players(self):
        """
        Get list of players already in database
        
        Returns:
            Set of FanGraphs IDs already loaded
        """
        session = get_session()
        
        try:
            result = session.execute(text("SELECT fg_id FROM players WHERE fg_id IS NOT NULL"))
            existing_ids = {row[0] for row in result}
            print(f"📊 Found {len(existing_ids)} players already in database")
            return existing_ids
        finally:
            session.close()
    
    def discover_active_players(self, seasons=[2023, 2024, 2025], min_pa=50):
        """
        Discover all qualified players from recent seasons
        
        Args:
            seasons: List of seasons to check
            min_pa: Minimum plate appearances to qualify
        
        Returns:
            DataFrame with unique players
        """
        all_players = []
        
        print("=" * 70)
        print("DISCOVERING ACTIVE MLB PLAYERS")
        print("=" * 70)
        
        for season in seasons:
            print(f"\n🔍 Fetching {season} qualified batters (min {min_pa} PA)...")
            
            try:
                stats = batting_stats(season, qual=min_pa)
                
                if stats is not None and not stats.empty:
                    # Extract player names
                    players_df = stats[['Name', 'Team', 'PA', 'wRC+']].copy()
                    players_df['Season'] = season
                    all_players.append(players_df)
                    
                    print(f"   ✅ Found {len(stats)} players")
                else:
                    print(f"   ⚠️  No data for {season}")
                    
            except Exception as e:
                print(f"   ❌ Error fetching {season}: {e}")
        
        if not all_players:
            print("\n❌ No players discovered")
            return pd.DataFrame()
        
        # Combine all seasons
        combined = pd.concat(all_players, ignore_index=True)
        
        # Get unique players (played in any season)
        unique_players = combined.groupby('Name').agg({
            'PA': 'sum',
            'wRC+': 'mean',
            'Season': lambda x: list(set(x))
        }).reset_index()
        
        # Sort by total PA (most active players first)
        unique_players = unique_players.sort_values('PA', ascending=False)
        
        print(f"\n✅ Discovered {len(unique_players)} unique players")
        print(f"   Total PA range: {unique_players['PA'].min():.0f} - {unique_players['PA'].max():.0f}")
        
        return unique_players
    
    def lookup_player_ids_batch(self, player_names, batch_size=50):
        """
        Look up FanGraphs IDs for discovered players in batches
        
        Args:
            player_names: List of player names
            batch_size: Number of players to lookup at once
        
        Returns:
            List of player dicts with IDs
        """
        all_results = []
        total = len(player_names)
        
        print(f"\n🔍 Looking up FanGraphs IDs for {total} players...")
        print(f"   Processing in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = player_names[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} players)")
            
            # Convert names to (first, last) tuples
            name_tuples = []
            for name in batch:
                parts = name.split(' ', 1)
                if len(parts) == 2:
                    name_tuples.append((parts[0], parts[1]))
                else:
                    # Single name or unusual format
                    name_tuples.append((parts[0], ''))
            
            # Lookup batch
            batch_results = self.bridge.bulk_id_lookup(name_tuples)
            all_results.extend(batch_results)
        
        print(f"\n✅ Successfully found IDs for {len(all_results)}/{total} players")
        print(f"   Success rate: {len(all_results)/total*100:.1f}%")
        
        return all_results
    
    def filter_new_players(self, discovered_players, existing_fg_ids):
        """
        Filter out players already in database
        
        Args:
            discovered_players: List of player dicts from lookup
            existing_fg_ids: Set of FanGraphs IDs already in DB
        
        Returns:
            List of new players to add
        """
        new_players = [p for p in discovered_players if p['fg_id'] not in existing_fg_ids]
        
        print(f"\n🆕 Found {len(new_players)} new players to add")
        print(f"   {len(discovered_players) - len(new_players)} already in database")
        
        return new_players
    
    def export_player_list(self, players, filename='discovered_active_players.txt'):
        """
        Export player list for review and batch loading
        
        Args:
            players: List of player dicts
            filename: Output filename
        """
        output_path = project_root / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Discovered Active MLB Players\n")
            f.write(f"# Total: {len(players)} players\n")
            f.write(f"# Generated: {pd.Timestamp.now()}\n\n")
            
            for i, player in enumerate(players, 1):
                f.write(f"{i:3d}. {player['name']:30s} FG ID: {player['fg_id']:6s}")
                if player.get('last_season'):
                    f.write(f"  Last: {player['last_season']}")
                f.write("\n")
        
        print(f"\n📝 Exported to {filename}")
        print(f"   Review the list before batch loading")
        return output_path
    
    def export_verified_players_format(self, players, filename='new_verified_players.py'):
        """
        Export in verified_players.py format for easy merging
        
        Args:
            players: List of player dicts
            filename: Output filename
        """
        output_path = project_root / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('"""\n')
            f.write('New players discovered via automated discovery\n')
            f.write(f'Generated: {pd.Timestamp.now()}\n')
            f.write(f'Total: {len(players)} players\n')
            f.write('"""\n\n')
            f.write('NEW_ACTIVE_PLAYERS = [\n')
            
            for player in players:
                f.write(f'    ("{player["name"]}", "{player["fg_id"]}"),\n')
            
            f.write(']\n')
        
        print(f"\n📝 Exported verified players format to {filename}")
        return output_path
    
    def run_full_discovery(self, seasons=[2023, 2024, 2025], min_pa=50):
        """
        Run complete discovery pipeline
        
        Returns:
            List of new players to add
        """
        print("\n" + "=" * 70)
        print("FULL ACTIVE PLAYER DISCOVERY PIPELINE")
        print("=" * 70)
        
        # Step 1: Get existing players
        existing_ids = self.get_existing_players()
        
        # Step 2: Discover active players from recent seasons
        discovered = self.discover_active_players(seasons, min_pa)
        
        if discovered.empty:
            return []
        
        # Step 3: Lookup FanGraphs IDs
        player_names = discovered['Name'].tolist()
        players_with_ids = self.lookup_player_ids_batch(player_names, batch_size=50)
        
        # Step 4: Filter new players
        new_players = self.filter_new_players(players_with_ids, existing_ids)
        
        # Step 5: Export results
        if new_players:
            self.export_player_list(new_players)
            self.export_verified_players_format(new_players)
            
            print("\n" + "=" * 70)
            print("DISCOVERY COMPLETE")
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"   Existing players: {len(existing_ids)}")
            print(f"   Discovered players: {len(discovered)}")
            print(f"   Successfully looked up: {len(players_with_ids)}")
            print(f"   New to add: {len(new_players)}")
            print(f"   Final database size: {len(existing_ids) + len(new_players)}")
            
            print(f"\n🎯 Next Steps:")
            print(f"   1. Review discovered_active_players.txt")
            print(f"   2. Run batch loading script to add players:")
            print(f"      python src/scripts/load_discovered_players.py")
        else:
            print("\n✅ No new players to add - database is up to date!")
        
        return new_players


def run_discovery_with_options():
    """
    Interactive discovery with user options
    """
    print("=" * 70)
    print("ACTIVE PLAYER DISCOVERY")
    print("=" * 70)
    print()
    print("This will discover all qualified MLB players from recent seasons")
    print("and identify which ones are not yet in the database.\n")
    
    # Get options from user
    print("Configuration:")
    print("1. Seasons to scan: 2023, 2024, 2025 (default)")
    print("2. Minimum PA threshold: 50 (default)")
    print()
    
    response = input("Use default settings? (yes/no): ").strip().lower()
    
    if response == 'yes' or response == 'y':
        seasons = [2023, 2024, 2025]
        min_pa = 50
    else:
        # Custom settings
        seasons_input = input("Seasons (comma-separated, e.g., 2023,2024,2025): ").strip()
        seasons = [int(s.strip()) for s in seasons_input.split(',')]
        
        min_pa_input = input("Minimum PA (e.g., 50): ").strip()
        min_pa = int(min_pa_input) if min_pa_input else 50
    
    print(f"\n📋 Configuration:")
    print(f"   Seasons: {', '.join(map(str, seasons))}")
    print(f"   Minimum PA: {min_pa}")
    print()
    
    response = input("Proceed with discovery? (yes/no): ").strip().lower()
    
    if response != 'yes' and response != 'y':
        print("Cancelled.")
        return
    
    # Run discovery
    discovery = ActivePlayerDiscovery()
    new_players = discovery.run_full_discovery(seasons, min_pa)
    
    if new_players:
        print(f"\n✨ Ready to add {len(new_players)} new players!")


if __name__ == "__main__":
    run_discovery_with_options()
