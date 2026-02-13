"""
Load verified players into database
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.verified_players import get_new_verified_players
from src.scripts.expand_player_database import PlayerDatabaseExpander

def load_verified():
    """Load all verified players that aren't in database yet"""
    
    expander = PlayerDatabaseExpander()
    
    try:
        # Get existing players
        existing = expander.get_existing_players()
        existing_ids = set(existing.keys())
        
        print(f"📊 Current database: {len(existing_ids)} players")
        
        # Get new verified players
        new_players = get_new_verified_players(existing_ids)
        
        print(f"📋 Found {len(new_players)} new verified players to add\n")
        
        if not new_players:
            print("✅ All verified players already loaded!")
            return
        
        # Ask for confirmation
        response = input(f"Load {len(new_players)} players? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Load them
        results = expander.add_players_batch(
            new_players,
            start_year=2015,
            end_year=2025,
            test_first=False,  # Already verified
            delay=2
        )
        
        # Summary
        print("\n" + "=" * 70)
        print("VERIFIED PLAYERS LOADED")
        print("=" * 70)
        print(f"✅ Successful: {len(results['successful'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        
        if results['failed']:
            print(f"\n⚠️  Failures (may need ID verification):")
            for name, fg_id, error in results['failed']:
                print(f"   - {name} (ID: {fg_id}): {error}")
        
        total = len(existing_ids) + len(results['successful'])
        print(f"\n📊 Total players in database: {total}")
        
    finally:
        expander.close()

if __name__ == "__main__":
    print("=" * 70)
    print("LOAD VERIFIED PLAYERS")
    print("=" * 70)
    print()
    
    load_verified()