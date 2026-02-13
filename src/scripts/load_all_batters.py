"""
Load all active MLB batters using Razzball's verified ID mapping
"""
import sys
from pathlib import Path
import json
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.player_id_resolver import get_active_batters
from src.scrapers.batch_scraper import scrape_multiple_players

def load_progress():
    """Load progress from file if it exists"""
    progress_file = 'batter_load_progress.json'
    if Path(progress_file).exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'completed_ids': [], 'failed': []}

def save_progress(progress):
    """Save progress to file"""
    with open('batter_load_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    print("=" * 60)
    print("Load All Active MLB Batters")
    print("=" * 60)
    
    # Get all active batters from Razzball data
    print("\n🔍 Loading verified player IDs from Razzball...")
    all_batters = get_active_batters()
    
    print(f"\n✅ Found {len(all_batters)} active batters")
    
    # Check for existing progress
    progress = load_progress()
    completed_ids = set(progress.get('completed_ids', []))
    
    # Filter out already completed players
    remaining_batters = [
        (name, fg_id) for name, fg_id in all_batters 
        if fg_id not in completed_ids
    ]
    
    if len(remaining_batters) < len(all_batters):
        print(f"\n📋 Resume mode: {len(completed_ids)} already loaded")
        print(f"   {len(remaining_batters)} remaining to load")
    
    if not remaining_batters:
        print("\n✅ All batters already loaded!")
        return
    
    print(f"\n📊 Configuration:")
    print(f"   Total batters: {len(all_batters)}")
    print(f"   Remaining: {len(remaining_batters)}")
    print(f"   Year range: 2015-2025")
    print(f"   Delay between requests: 2 seconds")
    print(f"   Estimated time: ~{len(remaining_batters) * 2 / 60:.0f} minutes")
    
    print("\n⚠️  This will take a while (~30 min for all 803 players)")
    print("   The script can be interrupted (Ctrl+C) and resumed later.")
    response = input("\nPress Enter to start, or Ctrl+C to cancel...")
    
    # Process in batches of 50 for better progress tracking
    batch_size = 50
    total_batches = (len(remaining_batters) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(remaining_batters))
        batch = remaining_batters[start_idx:end_idx]
        
        print(f"\n{'=' * 60}")
        print(f"BATCH {batch_num + 1}/{total_batches}")
        print(f"Players {start_idx + 1}-{end_idx} of {len(remaining_batters)}")
        print(f"{'=' * 60}")
        
        # Run batch scraper
        results = scrape_multiple_players(
            batch,
            start_year=2015,
            end_year=2025,
            delay=2
        )
        
        # Update progress - add successfully loaded FG IDs
        for name, player_id in results['success']:
            # Find the FG ID from the batch
            fg_id = next((fid for n, fid in batch if n == name), None)
            if fg_id:
                completed_ids.add(fg_id)
        
        # Save progress after each batch
        progress['completed_ids'] = list(completed_ids)
        progress['failed'] = progress.get('failed', []) + results['failed']
        progress['last_updated'] = datetime.now().isoformat()
        progress['batch_completed'] = batch_num + 1
        save_progress(progress)
        
        print(f"\n✅ Batch {batch_num + 1}/{total_batches} complete")
        print(f"   Total loaded so far: {len(completed_ids)}/{len(all_batters)}")
        print(f"   Progress: {len(completed_ids)/len(all_batters)*100:.1f}%")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 MASS LOAD COMPLETE!")
    print("=" * 60)
    print(f"✅ Successfully loaded: {len(completed_ids)}/{len(all_batters)}")
    print(f"❌ Failed: {len(progress.get('failed', []))}")
    print(f"📊 Success rate: {len(completed_ids)/len(all_batters)*100:.1f}%")
    
    if progress.get('failed'):
        print(f"\n⚠️  Failed players saved to batter_load_progress.json")
        
        # Show top 10 failures
        print(f"\n   Top failures:")
        for i, (name, error) in enumerate(progress['failed'][:10], 1):
            error_short = error[:60] + "..." if len(error) > 60 else error
            print(f"   {i}. {name}: {error_short}")
    
    # Save final results
    with open('final_batter_load_results.txt', 'w') as f:
        f.write(f"Mass Batter Load Results - {datetime.now()}\n")
        f.write(f"=" * 60 + "\n\n")
        f.write(f"Total batters: {len(all_batters)}\n")
        f.write(f"Successfully loaded: {len(completed_ids)}\n")
        f.write(f"Failed: {len(progress.get('failed', []))}\n")
        f.write(f"Success rate: {len(completed_ids)/len(all_batters)*100:.1f}%\n\n")
        
        if progress.get('failed'):
            f.write("Failed Players:\n")
            for name, error in progress['failed']:
                f.write(f"  - {name}: {error}\n")
    
    print(f"\n📝 Final results saved to final_batter_load_results.txt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted! Progress has been saved.")
        print("   Run this script again to resume from where you left off.")