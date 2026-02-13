"""
Interactive tool to add players using pybaseball
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.pybaseball_bridge import PybaseballBridge
from src.scrapers.fangraphs import scrape_player_season_stats, parse_fangraphs_columns
from src.database.insert_data import load_player_to_database
import time


def interactive_add_players():
    """
    Interactive player addition using pybaseball
    """
    
    bridge = PybaseballBridge()
    
    print("=" * 70)
    print("ADD PLAYERS USING PYBASEBALL")
    print("=" * 70)
    print()
    print("Enter player names to add. Type 'done' when finished.\n")
    
    players_to_add = []
    
    while True:
        first_name = input("First name (or 'done'): ").strip()
        
        if first_name.lower() == 'done':
            break
        
        last_name = input("Last name: ").strip()
        
        if first_name and last_name:
            players_to_add.append((first_name, last_name))
            print(f"  ✓ Added to queue: {first_name} {last_name}\n")
    
    if not players_to_add:
        print("No players added.")
        return
    
    print(f"\n🔍 Looking up {len(players_to_add)} players...")
    
    # Look up IDs
    player_info = bridge.bulk_id_lookup(players_to_add)
    
    if not player_info:
        print("❌ No valid players found with FanGraphs IDs")
        return
    
    print(f"\n✅ Found {len(player_info)} players with FanGraphs IDs")
    print("\nPlayers to load:")
    for i, p in enumerate(player_info, 1):
        print(f"  {i}. {p['name']} (FG ID: {p['fg_id']})")
    
    response = input(f"\nLoad these {len(player_info)} players? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Load each player
    print("\n" + "=" * 70)
    print("LOADING PLAYERS")
    print("=" * 70)
    
    successful = 0
    failed = []
    
    for i, player in enumerate(player_info, 1):
        print(f"\n[{i}/{len(player_info)}] {player['name']}...")
        
        try:
            # Scrape stats
            print(f"   Scraping 2015-2025...")
            
            # Temporarily add to player map
            import src.scrapers.fangraphs as fg_module
            original_map = fg_module.get_fangraphs_playerid_map
            
            def temp_map():
                return {player['name']: player['fg_id']}
            
            fg_module.get_fangraphs_playerid_map = temp_map
            
            data = scrape_player_season_stats(player['name'], 2015, 2025)
            
            # Restore
            fg_module.get_fangraphs_playerid_map = original_map
            
            if data is None or data.empty:
                print(f"   ⚠️  No data found")
                failed.append((player['name'], "No data"))
                continue
            
            # Parse and load
            cleaned = parse_fangraphs_columns(data)
            load_player_to_database(player['name'], player['fg_id'], cleaned)
            
            print(f"   ✅ Success! Loaded {len(cleaned)} seasons")
            successful += 1
            
            # Rate limiting
            if i < len(player_info):
                time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed.append((player['name'], str(e)))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully loaded: {successful}/{len(player_info)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\nFailed players:")
        for name, error in failed:
            print(f"  - {name}: {error}")


if __name__ == "__main__":
    interactive_add_players()