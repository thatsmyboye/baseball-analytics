"""
Audit codebase for duplicate or obsolete scripts
"""
from pathlib import Path
from collections import defaultdict
import ast

def find_similar_scripts():
    """Find potentially duplicate scripts"""
    
    project_root = Path(__file__).parent.parent.parent
    scripts_dir = project_root / 'src' / 'scripts'
    
    if not scripts_dir.exists():
        print("No scripts directory found")
        return
    
    scripts = list(scripts_dir.glob('*.py'))
    
    print("=" * 70)
    print(f"CODE AUDIT - {len(scripts)} scripts found")
    print("=" * 70)
    
    # Group by similar names
    name_groups = defaultdict(list)
    
    for script in scripts:
        # Extract base name patterns
        base = script.stem
        
        # Look for patterns like test_, debug_, old_, etc.
        if any(prefix in base for prefix in ['test', 'debug', 'old', 'temp', 'backup']):
            name_groups['temporary'].append(script)
        elif 'player' in base and 'add' in base:
            name_groups['player_addition'].append(script)
        elif 'discover' in base or 'investigate' in base or 'check' in base:
            name_groups['discovery'].append(script)
        else:
            name_groups['core'].append(script)
    
    # Report
    print("\n📊 SCRIPT CATEGORIES:\n")
    
    for category, scripts in name_groups.items():
        print(f"{category.upper()}:")
        for script in scripts:
            print(f"  - {script.name}")
        print()
    
    # Recommendations
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if name_groups['temporary']:
        print("\n⚠️  REVIEW TEMPORARY SCRIPTS:")
        print("These might be obsolete:")
        for script in name_groups['temporary']:
            print(f"  - {script.name}")
    
    if len(name_groups['discovery']) > 3:
        print("\n⚠️  MANY DISCOVERY SCRIPTS:")
        print("Consider consolidating these into one ID finder tool:")
        for script in name_groups['discovery']:
            print(f"  - {script.name}")
    
    if len(name_groups['player_addition']) > 2:
        print("\n⚠️  MULTIPLE PLAYER ADDITION SCRIPTS:")
        print("Consider keeping only:")
        print("  - load_verified_players.py (recommended)")
        print("  - expand_player_database.py (advanced)")

if __name__ == "__main__":
    find_similar_scripts()