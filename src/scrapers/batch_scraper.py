import time
from src.scrapers.fangraphs import scrape_player_season_stats, parse_fangraphs_columns, get_fangraphs_playerid_map
from src.database.insert_data import load_player_to_database

def scrape_multiple_players(player_list, start_year=2015, end_year=2025, delay=2):
    """
    Scrape and load multiple players to the database
    
    Args:
        player_list: List of tuples (player_name, fg_id)
        start_year: First season to scrape
        end_year: Last season to scrape
        delay: Seconds to wait between requests (be nice to FanGraphs)
    
    Returns:
        Summary dict with success/failure counts
    """
    
    results = {
        'success': [],
        'failed': [],
        'total': len(player_list)
    }
    
    print(f"🔄 Starting batch scrape for {len(player_list)} players...")
    print("=" * 60)
    
    for i, (player_name, fg_id) in enumerate(player_list, 1):
        print(f"\n[{i}/{len(player_list)}] Processing {player_name}...")
        
        try:
            # Scrape data
            data = scrape_player_season_stats(player_name, start_year, end_year)
            
            if data is None or data.empty:
                print(f"   ⚠️  No data found for {player_name}")
                results['failed'].append((player_name, "No data found"))
                continue
            
            # Parse to database format
            cleaned = parse_fangraphs_columns(data)
            
            # Load to database
            player_id = load_player_to_database(player_name, fg_id, cleaned)
            
            results['success'].append((player_name, player_id))
            
            # Be nice to FanGraphs servers
            if i < len(player_list):
                print(f"   ⏳ Waiting {delay}s before next request...")
                time.sleep(delay)
            
        except Exception as e:
            print(f"   ❌ Error processing {player_name}: {e}")
            results['failed'].append((player_name, str(e)))
            
            # Still wait before next request
            if i < len(player_list):
                time.sleep(delay)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 BATCH SCRAPE SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully loaded: {len(results['success'])}/{results['total']}")
    print(f"❌ Failed: {len(results['failed'])}/{results['total']}")
    
    if results['failed']:
        print("\nFailed players:")
        for name, error in results['failed']:
            print(f"  - {name}: {error}")
    
    return results


if __name__ == "__main__":
    # Test with a few star players
    test_players = [
        ("Harrison Bader", "18030"),
        ("Mike Trout", "10155"),
        ("Aaron Judge", "15640"),
        ("Shohei Ohtani", "19755"),
        ("Juan Soto", "21483"),
    ]
    
    print("=" * 60)
    print("Testing Batch Scraper - 5 Star Players")
    print("=" * 60)
    
    results = scrape_multiple_players(test_players, start_year=2015, end_year=2025, delay=2)
    
    print(f"\n🎉 Batch scrape complete!")
    print(f"   {len(results['success'])} players loaded successfully")