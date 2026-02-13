"""
Scrape FanGraphs leaderboard to get player IDs and stats
Uses actual HTML scraping instead of unreliable internal endpoints
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_leaderboard_page(season=2025, min_pa=100, page=1):
    """
    Scrape one page of FanGraphs batting leaderboard
    
    Args:
        season: Season year
        min_pa: Minimum plate appearances
        page: Page number
    
    Returns:
        DataFrame with player data including playerids
    """
    
    # FanGraphs leaderboard URL
    url = "https://www.fangraphs.com/leaders.aspx"
    
    params = {
        'pos': 'all',
        'stats': 'bat',
        'lg': 'all',
        'qual': str(min_pa),
        'type': 'c',
        'season': str(season),
        'month': '0',
        'season1': str(season),
        'ind': '0',
        'team': '0',
        'rost': '0',
        'age': '0',
        'filter': '',
        'players': '0',
        'startdate': '',
        'enddate': '',
        'page': f'{page}_50',  # Page_ItemsPerPage format
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the leaderboard table
        table = soup.find('table', {'class': 'rgMasterTable'})
        
        if not table:
            print("Could not find leaderboard table")
            return None
        
        # Extract player links (contain playerids)
        players = []
        
        rows = table.find_all('tr')[1:]  # Skip header
        
        for row in rows:
            # Find player link
            player_link = row.find('a', href=lambda x: x and '/players/' in x)
            
            if player_link:
                # Extract playerid from URL
                # Format: /players/player-name/12345/stats
                href = player_link['href']
                parts = href.split('/')
                
                if len(parts) >= 4:
                    playerid = parts[3]
                    player_name = player_link.text.strip()
                    
                    # Get team
                    team_cell = row.find_all('td')[2] if len(row.find_all('td')) > 2 else None
                    team = team_cell.text.strip() if team_cell else 'N/A'
                    
                    players.append({
                        'name': player_name,
                        'playerid': playerid,
                        'team': team,
                        'url': f"https://www.fangraphs.com{href}"
                    })
        
        return pd.DataFrame(players)
        
    except Exception as e:
        print(f"Error scraping page {page}: {e}")
        return None


def get_all_active_players(season=2025, min_pa=50, max_pages=10):
    """
    Scrape multiple pages to get all active players
    
    Returns:
        DataFrame with all players and their IDs
    """
    
    all_players = []
    
    print(f"🔍 Scraping FanGraphs {season} leaderboard (min {min_pa} PA)...")
    
    for page in range(1, max_pages + 1):
        print(f"   Page {page}...", end=' ')
        
        df = scrape_leaderboard_page(season, min_pa, page)
        
        if df is None or df.empty:
            print("No more data")
            break
        
        all_players.append(df)
        print(f"{len(df)} players")
        
        time.sleep(1)  # Be nice to FanGraphs
    
    if all_players:
        combined = pd.concat(all_players, ignore_index=True)
        
        # Remove duplicates
        combined = combined.drop_duplicates(subset=['playerid'])
        
        print(f"\n✅ Found {len(combined)} unique players")
        
        return combined
    
    return None


def save_player_mapping(df, filename='fangraphs_player_ids.csv'):
    """Save player ID mapping to CSV"""
    if df is not None:
        df.to_csv(filename, index=False)
        print(f"📝 Saved to {filename}")


if __name__ == "__main__":
    print("=" * 70)
    print("FANGRAPHS LEADERBOARD SCRAPER")
    print("=" * 70)
    print()
    
    # Get all players from 2025 with at least 50 PA
    players_df = get_all_active_players(season=2025, min_pa=50, max_pages=10)
    
    if players_df is not None:
        print("\n📊 Sample players:")
        print(players_df.head(10).to_string(index=False))
        
        # Save to CSV
        save_player_mapping(players_df)
        
        print(f"\n💡 You can now use these playerids to load players into your database!")
        print(f"   Total players available: {len(players_df)}")