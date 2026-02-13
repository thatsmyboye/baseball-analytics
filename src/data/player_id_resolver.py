"""
Player ID resolver using Razzball's comprehensive ID mapping
"""
import pandas as pd
from pathlib import Path

def load_razzball_mapping(csv_path='src/data/razzball.csv'):
    """
    Load Razzball player ID mapping
    
    Returns:
        DataFrame with player names and IDs
    """
    df = pd.read_csv(csv_path, encoding='utf-8-sig')  # Handle BOM
    
    # Filter for players with valid FanGraphs IDs (numeric only)
    df = df[df['FanGraphsID'].notna()]
    
    # Convert to string first, then filter for numeric values only
    df['FanGraphsID'] = df['FanGraphsID'].astype(str)
    df = df[df['FanGraphsID'].str.isnumeric()]
    
    # Clean up the data
    df['Name'] = df['Name'].str.strip()
    
    print(f"✅ Loaded {len(df)} players with valid FanGraphs IDs")
    
    return df

def get_active_batters(csv_path='src/data/razzball.csv', exclude_pitchers=True):
    """
    Get all active position players (exclude pitchers)
    
    Returns:
        List of tuples: (player_name, fg_id)
    """
    df = load_razzball_mapping(csv_path)
    
    if exclude_pitchers:
        # Exclude players whose primary position is pitcher
        pitcher_positions = ['P', 'SP', 'RP']
        df = df[~df['STD_POS'].isin(pitcher_positions)]
    
    # Convert to list of tuples
    players = list(zip(df['Name'], df['FanGraphsID']))
    
    print(f"✅ Found {len(players)} active batters")
    
    return players

def search_player(name, csv_path='src/data/razzball.csv'):
    """
    Search for a specific player by name
    
    Returns:
        (player_name, fg_id) or None
    """
    df = load_razzball_mapping(csv_path)
    
    # Case-insensitive search
    matches = df[df['Name'].str.contains(name, case=False, na=False)]
    
    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        row = matches.iloc[0]
        return (row['Name'], str(row['FanGraphsID']))
    else:
        # Multiple matches - return exact match if exists
        exact = matches[matches['Name'].str.lower() == name.lower()]
        if len(exact) == 1:
            row = exact.iloc[0]
            return (row['Name'], str(row['FanGraphsID']))
        else:
            # Return first match
            row = matches.iloc[0]
            return (row['Name'], str(row['FanGraphsID']))

if __name__ == "__main__":
    print("=" * 60)
    print("Razzball Player ID Resolver")
    print("=" * 60)
    
    # Test loading
    df = load_razzball_mapping()
    
    print("\n📊 Sample players:")
    sample = df.head(10)
    for _, row in sample.iterrows():
        print(f"   {row['Name']} ({row['Team']}) - FG ID: {row['FanGraphsID']}")
    
    # Get all active batters
    batters = get_active_batters()
    print(f"\n✅ Total active batters: {len(batters)}")
    
    # Test search
    print("\n🔍 Testing search:")
    result = search_player("Aaron Judge")
    if result:
        print(f"   Found: {result[0]} (ID: {result[1]})")