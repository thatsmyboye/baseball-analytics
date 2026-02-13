"""
Load top MLB players into the database
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.player_list import get_players_by_count
from src.scrapers.batch_scraper import scrape_multiple_players

def main():
    print("=" * 60)
    print("Loading Top MLB Players to Database")
    print("=" * 60)
    
    # Start with top 50 players
    players = get_players_by_count(50)
    
    print(f"\n📋 Preparing to load {len(players)} players")
    print(f"   Year range: 2015-2025")
    print(f"   Delay between requests: 2 seconds")
    
    input("\nPress Enter to start, or Ctrl+C to cancel...")
    
    # Run batch scraper
    results = scrape_multiple_players(
        players, 
        start_year=2015, 
        end_year=2025, 
        delay=2
    )
    
    print(f"\n✅ Complete! {len(results['success'])} players loaded")
    
    # Save results to file
    with open('load_results.txt', 'w') as f:
        f.write(f"Successfully loaded: {len(results['success'])}\n")
        f.write(f"Failed: {len(results['failed'])}\n\n")
        
        if results['failed']:
            f.write("Failed players:\n")
            for name, error in results['failed']:
                f.write(f"  {name}: {error}\n")
    
    print("📝 Results saved to load_results.txt")

if __name__ == "__main__":
    main()