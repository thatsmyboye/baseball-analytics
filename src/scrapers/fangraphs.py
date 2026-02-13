import requests
import pandas as pd
import time
import re

def get_fangraphs_playerid_map():
    """
    Get mapping of player names to FanGraphs IDs
    """
    return {
        # Already loaded
        "Harrison Bader": "18030",
        "Kris Bryant": "15429",
        "Mike Trout": "10155",
        "Aaron Judge": "15640",
        "Shohei Ohtani": "19755",
        "Juan Soto": "21483",
        
        # Catchers
        "J.T. Realmuto": "11739",
        "Will Smith": "19197",
        "Salvador Perez": "7304",
        "Adley Rutschman": "25475",
        "Cal Raleigh": "21534",
        
        # First Base
        "Freddie Freeman": "5361",
        "Matt Olson": "14344",
        "Vladimir Guerrero Jr.": "19611",
        "Pete Alonso": "19251",
        "Paul Goldschmidt": "9218",
        
        # Second Base
        "Marcus Semien": "12533",
        "Jose Altuve": "5417",
        "Gleyber Torres": "16997",
        "Ozzie Albies": "16556",
        "Ketel Marte": "13613",
        
        # Shortstop
        "Bobby Witt Jr.": "25764",
        "Corey Seager": "11479",
        "Trea Turner": "13510",
        "Francisco Lindor": "12916",
        "Dansby Swanson": "16530",
        
        # Third Base
        "Jose Ramirez": "11493",
        "Rafael Devers": "17350",
        "Austin Riley": "18360",
        "Manny Machado": "11493",
        "Nolan Arenado": "9777",
        
        # Outfield
        "Mookie Betts": "13611",
        "Ronald Acuna Jr.": "18401",
        "Kyle Tucker": "18345",
        "Randy Arozarena": "19384",
        "Yordan Alvarez": "21318",
        "Fernando Tatis Jr.": "19709",
        "Julio Rodriguez": "23697",
        "Corbin Carroll": "25878",
        "Jazz Chisholm Jr.": "20454",
        "Kyle Schwarber": "14113",
        "Christian Yelich": "11477",
        "George Springer": "12856",
        "Teoscar Hernandez": "13066",
        "Bryan Reynolds": "19326",
        "Anthony Santander": "15711",
        "Ian Happ": "17919",
        "Cedric Mullins": "19363",
        "Steven Kwan": "24610",
        "Jesse Winker": "14916",
        "Michael Harris II": "25931",
        "Jarren Duran": "23273",
        "Riley Greene": "25696",
        
        # Additional IF
        "Gunnar Henderson": "26165",
        "Nico Hoerner": "21755",
        "Jorge Polanco": "12973",
        "Jonathan India": "23649",
        
        # DH / Utility
        "Giancarlo Stanton": "4949",
        "J.D. Martinez": "7173",
    }

def scrape_player_season_stats(player_name, start_year=2015, end_year=2025, mlb_only=True):
    """
    Scrape FanGraphs season stats for a specific player
    
    Args:
        player_name: Player's name (e.g., "Harrison Bader")
        start_year: First season to scrape
        end_year: Last season to scrape
        mlb_only: If True, filter out minor league seasons
    
    Returns:
        DataFrame with season stats (actual MLB regular season only)
        For multi-team seasons, includes both combined totals and individual splits
    """
    
    print(f"🔍 Looking up {player_name} on FanGraphs...")
    
    # Get player ID
    player_map = get_fangraphs_playerid_map()
    player_id = player_map.get(player_name)
    
    if not player_id:
        print(f"❌ Player ID not found for {player_name}")
        print(f"   Available players: {list(player_map.keys())}")
        return None
    
    print(f"   Player ID: {player_id}")
    
    # FanGraphs player stats API
    base_url = f"https://www.fangraphs.com/api/players/stats"
    
    params = {
        'playerid': player_id,
        'position': 'OF',
        'type': 'bat',
        'stats': 'bat',
        'season': end_year,
        'season1': start_year,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    try:
        print(f"   Fetching stats for {start_year}-{end_year}...")
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract stats data
        if 'data' in data:
            stats_data = data['data']
        else:
            stats_data = data
        
        if not stats_data:
            print(f"❌ No stats data found")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(stats_data)
        
        print(f"   Retrieved {len(df)} total rows")
        
        # Clean up HTML tags
        df = clean_html_tags(df)
        
        # Filter for MLB only
        if mlb_only:
            # Remove minor league levels
            if 'AbbLevel' in df.columns:
                minor_levels = ['R', 'A-', 'A', 'A+', 'AA', 'AAA', 'MiLB']
                df = df[~df['AbbLevel'].isin(minor_levels)]
        
        # Filter out league averages and projections
        exclude_teams = [
            'Average',
            'Steamer',
            'ZiPS',
            'ZiPS DC',
            'THE BAT',
            'THE BAT X',
            'ATC',
            'FanGraphs DC',
            'OOPSY DC',
        ]
        
        df = df[~df['Team'].isin(exclude_teams)]
        
        # Filter out postseason/playoff rows
        # Check type column if it exists
        if 'type' in df.columns:
            # Convert to string first to safely use .str accessor
            df['type'] = df['type'].astype(str)
            df = df[~df['type'].str.contains('post|playoff', case=False, na=False)]
        
        # Also check Team column for postseason indicators
        df = df[~df['Team'].str.contains('Postseason|- - -|playoff', case=False, na=False)]
        
        # Remove any row where Team contains projection keywords
        projection_keywords = ['Steamer', 'ZiPS', 'THE BAT', 'ATC', 'DC', 'OOPSY']
        for keyword in projection_keywords:
            df = df[~df['Team'].str.contains(keyword, case=False, na=False)]
        
        # Remove rows with NaN in critical columns
        df = df[df['G'].notna()]
        
        # Remove very small sample sizes (likely incomplete/erroneous data)
        df['G'] = pd.to_numeric(df['G'], errors='coerce')
        df = df[df['G'] >= 1]
        
        print(f"   Filtered to {len(df)} actual MLB regular season rows")
        
        if df.empty:
            print(f"❌ No actual MLB seasons found for {player_name}")
            return None
        
        # Remove rows with NaN in critical columns
        df = df[df['G'].notna()]
        
        # Convert to numeric for filtering
        df['G'] = pd.to_numeric(df['G'], errors='coerce')
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce')
        df['Season'] = pd.to_numeric(df['Season'], errors='coerce')
        
        # Remove duplicate season+team combinations (keeps the one with most games)
        # This filters out playoff rows which appear as small-sample duplicates
        df = df.sort_values(['Season', 'Team', 'G'], ascending=[True, True, False])
        df = df.drop_duplicates(subset=['Season', 'Team'], keep='first')
        
        # Remove very small sample sizes for remaining rows
        df = df[df['G'] >= 1]
        
        print(f"   Filtered to {len(df)} actual MLB regular season rows")
        
        # Sort by season, then by games (to put combined totals first for multi-team seasons)
        df['Season'] = pd.to_numeric(df['Season'], errors='coerce')
        df = df.sort_values(['Season', 'G'], ascending=[True, False])
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error scraping FanGraphs: {e}")
        import traceback
        traceback.print_exc()
        return None


def clean_html_tags(df):
    """
    Remove HTML tags from DataFrame columns
    """
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            # Remove HTML tags
            df[col] = df[col].astype(str).str.replace('<[^<]+?>', '', regex=True)
            # Clean up whitespace
            df[col] = df[col].str.strip()
    
    return df


def parse_fangraphs_columns(df):
    """
    Parse and clean FanGraphs column names to match our database schema
    """
    column_mapping = {
        'Season': 'season',
        'Team': 'team',
        'G': 'games',
        'PA': 'pa',
        'AB': 'ab',
        'H': 'hits',
        '2B': 'doubles',
        '3B': 'triples',
        'HR': 'hr',
        'R': 'runs',
        'RBI': 'rbi',
        'BB': 'bb',
        'SO': 'so',
        'SB': 'sb',
        'CS': 'cs',
        'AVG': 'avg',
        'OBP': 'obp',
        'SLG': 'slg',
        'wOBA': 'woba',
        'wRC+': 'wrc_plus',
        'BABIP': 'babip',
        'BB%': 'bb_pct',
        'K%': 'k_pct',
        'ISO': 'iso',
        'GB%': 'gb_pct',
        'FB%': 'fb_pct',
        'LD%': 'ld_pct',
        'HR/FB': 'hr_fb_pct',
    }
    
    # Rename columns that exist
    df_clean = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    
    # Convert numeric columns
    numeric_cols = ['season', 'games', 'pa', 'ab', 'hits', 'doubles', 'triples', 'hr', 
                    'runs', 'rbi', 'bb', 'so', 'avg', 'obp', 'slg', 'woba', 'wrc_plus', 
                    'babip', 'bb_pct', 'k_pct', 'iso', 'gb_pct', 'fb_pct', 'ld_pct', 'hr_fb_pct']
    
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    return df_clean


if __name__ == "__main__":
    # Test the scraper
    print("=" * 60)
    print("Testing FanGraphs Scraper - Harrison Bader")
    print("=" * 60)
    
    data = scrape_player_season_stats("Harrison Bader", 2015, 2025, mlb_only=True)
    
    if data is not None:
        print("\n📊 Available columns:")
        print(list(data.columns))
        
        print("\n📈 MLB Career Stats:")
        display_cols = [col for col in ['Season', 'Team', 'G', 'PA', 'AB', 'H', 'HR', 'AVG', 'OBP', 'SLG', 'wRC+', 'BABIP'] 
                       if col in data.columns]
        
        if display_cols:
            print(data[display_cols].to_string(index=False))
        else:
            print(data.head())
        
        print("\n📋 Parsing to database format...")
        cleaned = parse_fangraphs_columns(data)
        
        # Show what we'll insert into database
        db_cols = [col for col in ['season', 'team', 'games', 'pa', 'avg', 'obp', 'slg', 'wrc_plus', 'babip'] 
                   if col in cleaned.columns]
        
        if db_cols:
            print("\n🗄️  Database-ready format:")
            print(cleaned[db_cols].to_string(index=False))