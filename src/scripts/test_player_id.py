"""
Test if a FanGraphs ID works
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.fangraphs import scrape_player_season_stats

def test_id():
    """Interactive ID tester"""
    
    print("=" * 70)
    print("FANGRAPHS ID TESTER")
    print("=" * 70)
    print()
    
    player_name = input("Player name: ").strip()
    fg_id = input("FanGraphs ID to test: ").strip()
    
    if not player_name or not fg_id:
        print("Both fields required")
        return
    
    print(f"\n🔍 Testing ID {fg_id} for {player_name}...")
    
    # Temporarily add to player map
    import src.scrapers.fangraphs as fg_module
    original_map = fg_module.get_fangraphs_playerid_map
    
    def temp_map():
        return {player_name: fg_id}
    
    fg_module.get_fangraphs_playerid_map = temp_map
    
    try:
        # Try to scrape 2024 season
        data = scrape_player_season_stats(player_name, 2024, 2024)
        
        # Restore original
        fg_module.get_fangraphs_playerid_map = original_map
        
        if data is not None and not data.empty:
            print(f"\n✅ SUCCESS! ID {fg_id} works!")
            print(f"\nRetrieved data:")
            print(data[['Season', 'Team', 'G', 'PA', 'AVG', 'HR']].to_string(index=False))
            
            print(f"\n📝 Add this to src/data/verified_players.py:")
            print(f'    ("{player_name}", "{fg_id}"),')
            
            return True
        else:
            print(f"\n❌ FAILED: ID {fg_id} returned no data")
            return False
            
    except Exception as e:
        fg_module.get_fangraphs_playerid_map = original_map
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_id()
    
    print("\n" + "=" * 70)
    choice = input("\nTest another ID? (yes/no): ")
    
    if choice.lower() == 'yes':
        test_id()