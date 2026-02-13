"""
Load all active MLB players into the database
Includes resume capability and detailed logging
"""
import sys
from pathlib import Path
import json
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.discover_players import get_active_mlb_players
from src.scrapers.batch_scraper import scrape_multiple_players

def load_progress():
    """Load progress from file if it exists"""
    progress_file = 'load_progress.json'
    if Path(progress_file).exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'completed_ids': [], 'failed': []}

def save_progress(progress):
    """Save progress to file"""
    with open('load_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    print("=" * 60)
    print("Load All Active MLB Players")
    print("=" * 60)
    
    # Get all active players
    print("\n🔍 Discovering active players...")
    all_players = get_active_mlb_players(season=2025, min_pa=1)
    
    if not all_players:
        print("❌ No players found!")
        return
    
    print(f"\n✅ Found {len(all_players)} active players")
    
    # Check for existing progress
    progress = load_progress()
    completed_ids = set(progress.get('completed_ids', []))
    
    # Filter out already completed players
    remaining_players = [
        (name, fg_id) for name, fg_id in all_players 
        if fg_id not in completed_ids
    ]
    
    if len(remaining_players) < len(all_players):
        print(f"\n📋 Resume mode: {len(completed_ids)} already loaded")
        print(f"   {len(remaining_players)} remaining to load")
    
    if not remaining_players:
        print("\n✅ All players already loaded!")
        return
    
    print(f"\n📊 Configuration:")
    print(f"   Total players: {len(all_players)}")
    print(f"   Remaining: {len(remaining_players)}")
    print(f"   Year range: 2015-2025")
    print(f"   Delay between requests: 2 seconds")
    print(f"   Estimated time: ~{len(remaining_players) * 2 / 60:.0f} minutes")
    
    print("\n⚠️  This will take a while. The script can be interrupted and resumed.")
    response = input("\nPress Enter to start, or Ctrl+C to cancel...")
    
    # Process in batches of 50 for better progress tracking
    batch_size = 50
    total_batches = (len(remaining_players) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(remaining_players))
        batch = remaining_players[start_idx:end_idx]
        
        print(f"\n{'=' * 60}")
        print(f"BATCH {batch_num + 1}/{total_batches}")
        print(f"Players {start_idx + 1}-{end_idx} of {len(remaining_players)}")
        print(f"{'=' * 60}")
        
        # Run batch scraper
        results = scrape_multiple_players(
            batch,
            start_year=2015,
            end_year=2025,
            delay=2
        )
        
        # Update progress
        for name, player_id in results['success']:
            # Extract FG ID from the batch
            fg_id = next((fid for n, fid in batch if n == name), None)
            if fg_id:
                completed_ids.add(fg_id)
        
        # Save progress after each batch
        progress['completed_ids'] = list(completed_ids)
        progress['failed'] = progress.get('failed', []) + results['failed']
        progress['last_updated'] = datetime.now().isoformat()
        save_progress(progress)
        
        print(f"\n✅ Batch {batch_num + 1} complete")
        print(f"   Total loaded so far: {len(completed_ids)}/{len(all_players)}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 MASS LOAD COMPLETE!")
    print("=" * 60)
    print(f"✅ Successfully loaded: {len(completed_ids)}/{len(all_players)}")
    print(f"❌ Failed: {len(progress.get('failed', []))}")
    
    if progress.get('failed'):
        print(f"\n⚠️  Failed players saved to load_progress.json")
        print(f"   You can retry them later")
    
    # Save final results
    with open('final_load_results.txt', 'w') as f:
        f.write(f"Mass Load Results - {datetime.now()}\n")
        f.write(f"=" * 60 + "\n\n")
        f.write(f"Total players discovered: {len(all_players)}\n")
        f.write(f"Successfully loaded: {len(completed_ids)}\n")
        f.write(f"Failed: {len(progress.get('failed', []))}\n\n")
        
        if progress.get('failed'):
            f.write("Failed Players:\n")
            for name, error in progress['failed']:
                f.write(f"  - {name}: {error}\n")
    
    print(f"\n📝 Final results saved to final_load_results.txt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted! Progress has been saved.")
        print("   Run this script again to resume from where you left off.")