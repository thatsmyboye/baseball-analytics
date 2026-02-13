"""
Discover FanGraphs API IDs by testing player names

The FanGraphs API uses different IDs than their website URLs.
This tool helps find the correct API IDs by searching.
"""
import sys
from pathlib import Path
import requests
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def search_fangraphs_player(player_name):
    """
    Search for a player on FanGraphs and try to find their API ID
    
    Strategy: Use their search/autocomplete API
    """
    
    # Try the search endpoint
    search_url = "https://www.fangraphs.com/api/players/search"
    
    params = {
        'term': player_name,
        'active': 'true'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        if results:
            print(f"\n🔍 Search results for '{player_name}':")
            for i, player in enumerate(results[:5], 1):
                print(f"   {i}. {player.get('PlayerName', 'N/A')}")
                print(f"      ID: {player.get('playerid', 'N/A')}")
                print(f"      Team: {player.get('teamname', 'N/A')}")
                print(f"      Position: {player.get('position', 'N/A')}")
            
            return results
        else:
            print(f"❌ No results for '{player_name}'")
            return None
            
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return None


def verify_player_id(player_id, player_name):
    """
    Verify a player ID works with the stats API
    """
    from src.scrapers.fangraphs import scrape_player_season_stats
    
    try:
        # Create temporary player map
        import src.scrapers.fangraphs as fg_module
        original_map = fg_module.get_fangraphs_playerid_map
        
        def temp_map():
            return {player_name: str(player_id)}
        
        fg_module.get_fangraphs_playerid_map = temp_map
        
        # Try to scrape
        data = scrape_player_season_stats(player_name, 2024, 2024)
        
        # Restore original
        fg_module.get_fangraphs_playerid_map = original_map
        
        if data is not None and not data.empty:
            print(f"   ✅ ID {player_id} WORKS!")
            return True
        else:
            print(f"   ❌ ID {player_id} returned no data")
            return False
            
    except Exception as e:
        print(f"   ❌ ID {player_id} failed: {e}")
        return False


def interactive_discovery():
    """
    Interactive tool to discover player IDs
    """
    print("=" * 70)
    print("FANGRAPHS API ID DISCOVERY TOOL")
    print("=" * 70)
    print()
    print("This tool helps find the correct FanGraphs API IDs for players.")
    print("Enter player names to search and test IDs.")
    print("Type 'quit' to exit.\n")
    
    discovered = []
    
    while True:
        player_name = input("Player name (or 'quit'): ").strip()
        
        if player_name.lower() == 'quit':
            break
        
        if not player_name:
            continue
        
        # Search for player
        results = search_fangraphs_player(player_name)
        
        if not results:
            continue
        
        # Ask which result to test
        print("\nWhich result to test? (1-5, or 'all', or 'skip'): ", end='')
        choice = input().strip()
        
        if choice.lower() == 'skip':
            continue
        
        to_test = []
        if choice.lower() == 'all':
            to_test = results[:5]
        elif choice.isdigit() and 1 <= int(choice) <= min(5, len(results)):
            to_test = [results[int(choice) - 1]]
        else:
            print("Invalid choice")
            continue
        
        # Test each
        for player in to_test:
            player_id = player.get('playerid')
            name = player.get('PlayerName')
            
            if player_id:
                print(f"\nTesting {name} (ID: {player_id})...")
                if verify_player_id(player_id, name):
                    discovered.append((name, str(player_id)))
        
        print()
    
    # Summary
    if discovered:
        print("\n" + "=" * 70)
        print(f"DISCOVERED {len(discovered)} WORKING IDs")
        print("=" * 70)
        print("\nAdd these to src/data/verified_players.py:")
        print()
        for name, player_id in discovered:
            print(f'    ("{name}", "{player_id}"),')
    else:
        print("\nNo new IDs discovered.")


if __name__ == "__main__":
    interactive_discovery()