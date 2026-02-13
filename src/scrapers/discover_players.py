import requests
import pandas as pd
import time

def get_active_mlb_players(season=2025, min_pa=1):
    """
    Get all active MLB players from FanGraphs leaderboard
    
    Args:
        season: Season to check for active players
        min_pa: Minimum plate appearances (1 = anyone who played)
    
    Returns:
        List of tuples: (player_name, fg_id)
    """
    
    print(f"🔍 Discovering active MLB players from {season} season...")
    
    # FanGraphs API endpoint for leaderboard data
    base_url = "https://www.fangraphs.com/api/leaders/major-league/data"
    
    params = {
        'pos': 'all',
        'stats': 'bat',
        'lg': 'all',
        'qual': str(min_pa),  # Minimum PA
        'type': 'c',  # Standard batting
        'season': season,
        'month': '0',
        'season1': season,
        'ind': '0',  # Combined season (not split)
        'team': '0',
        'rost': '0',
        'age': '0',
        'filter': '',
        'players': '0',
        'startdate': '',
        'enddate': '',
        'pageitems': '50',
        'pagenum': '1',
        'sortdir': 'desc',
        'sortstat': 'WAR'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    all_players = []
    page = 1
    
    try:
        while True:
            params['pagenum'] = str(page)
            
            print(f"   Fetching page {page}...")
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract player data from response
            if isinstance(data, dict) and 'data' in data:
                players = data['data']
            else:
                players = data
            
            if not players or len(players) == 0:
                break
            
            # Extract player info
            for player in players:
                if isinstance(player, dict):
                    player_name = player.get('PlayerName') or player.get('Name')
                    player_id = player.get('playerid') or player.get('PlayerId')
                    
                    if player_name and player_id:
                        all_players.append((player_name, str(player_id)))
            
            print(f"      Found {len(players)} players on page {page}")
            
            # If we got fewer than 50 results, we're done
            if len(players) < 50:
                break
            
            page += 1
            time.sleep(0.5)  # Be nice to FanGraphs
            
            # Safety limit
            if page > 50:
                print("   ⚠️  Reached page limit")
                break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_players = []
        for player in all_players:
            if player[1] not in seen:
                seen.add(player[1])
                unique_players.append(player)
        
        print(f"\n✅ Found {len(unique_players)} unique active players")
        return unique_players
        
    except Exception as e:
        print(f"❌ Error discovering players: {e}")
        import traceback
        traceback.print_exc()
        return []


def save_player_list(players, filename='active_players.txt'):
    """Save player list to file for reference"""
    with open(filename, 'w') as f:
        f.write(f"# Active MLB Players - {len(players)} total\n")
        f.write("# Format: Player Name | FanGraphs ID\n\n")
        for name, fg_id in players:
            f.write(f"{name} | {fg_id}\n")
    
    print(f"📝 Saved player list to {filename}")


if __name__ == "__main__":
    print("=" * 60)
    print("Active MLB Player Discovery")
    print("=" * 60)
    
    # Get all players with at least 1 PA in 2025
    players = get_active_mlb_players(season=2025, min_pa=1)
    
    if players:
        print(f"\n📊 Sample players:")
        for i, (name, fg_id) in enumerate(players[:10], 1):
            print(f"   {i}. {name} (ID: {fg_id})")
        
        print(f"\n   ... and {len(players) - 10} more")
        
        # Save to file
        save_player_list(players, 'active_players_2025.txt')
        
        print(f"\n🎯 Ready to load {len(players)} players!")