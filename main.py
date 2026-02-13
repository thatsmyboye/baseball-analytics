# Entry point
from src.utils.db_connection import init_database, get_session
from src.scrapers.fangraphs import scrape_player_season_stats

def main():
    print("🚀 Baseball Analytics - Initial Setup\n")
    
    # Step 1: Initialize database
    print("Step 1: Setting up database...")
    init_database()
    
    # Step 2: Test scraping Harrison Bader
    print("\nStep 2: Testing scraper with Harrison Bader...")
    bader_data = scrape_player_season_stats("Harrison Bader", 2015, 2025)
    
    if bader_data is not None:
        print("\n✅ Successfully scraped Harrison Bader's data!")
        print(f"   Seasons found: {len(bader_data)}")
        print("\n📊 Preview:")
        print(bader_data[['Season', 'Team', 'G', 'PA', 'AVG', 'OBP', 'SLG', 'wRC+']].to_string())
    else:
        print("\n❌ Failed to scrape data")

if __name__ == "__main__":
    main()