# Project Maintenance & Hygiene

Guide for keeping the project organized and removing outdated files.

## Monthly Maintenance Checklist

### 1. Identify Temporary/Debug Files

Run the cleanup script:
```bash
python src/scripts/cleanup_project.py
```

This will identify:
- Debug/test output files
- Temporary JSON files from scrapers
- Old log files
- Unused scripts

### 2. Archive Old Reports

Move dated reports to archive:
```bash
mkdir -p archive/reports
mv *_20*.txt archive/reports/
mv *_20*.json archive/reports/
```

### 3. Remove Duplicate/Obsolete Scripts

Check for duplicates:
```bash
python src/scripts/audit_codebase.py
```

---

## File Organization

### Keep These (Core System)
```
✅ src/analytics/          # Core analytics (never delete)
✅ src/automation/         # Daily automation (keep)
✅ src/database/           # Schema & loaders (keep)
✅ src/scrapers/          # Data pipeline (keep)
✅ src/utils/             # DB connection (keep)
✅ src/data/              # Verified players list (keep)
✅ docs/                  # Documentation (keep)
```

### Review These Periodically
```
⚠️ src/scripts/          # One-off utilities
   - Keep: test_player_id.py, deduplicate_players.py, add_birth_dates.py
   - Review: Everything else (check last use date)

⚠️ Root directory        # Reports and outputs
   - Delete: Files older than 30 days
   - Keep: README.md, requirements.txt, .env, .gitignore
```

### Delete These Immediately
```
❌ *.pyc, __pycache__/    # Python cache
❌ .DS_Store              # Mac files
❌ fangraphs_page.html    # Debug outputs
❌ daily_update_*.json    # Old scraper outputs (>7 days)
❌ *_test.py              # Temporary test files
❌ *.log                  # Old log files (>30 days)
```

---

## Cleanup Script

Create `src/scripts/cleanup_project.py`:
```python
"""
Project cleanup utility
Identifies temporary, debug, and outdated files
"""
import os
from pathlib import Path
from datetime import datetime, timedelta

def scan_for_cleanup():
    """Scan project for files that can be cleaned up"""
    
    project_root = Path(__file__).parent.parent.parent
    
    cleanup_candidates = {
        'debug_files': [],
        'old_reports': [],
        'temp_outputs': [],
        'cache_files': [],
    }
    
    # Scan root directory
    for file in project_root.glob('*'):
        if file.is_file():
            # Debug HTML files
            if file.suffix == '.html':
                cleanup_candidates['debug_files'].append(file)
            
            # Old dated reports (>30 days)
            if any(x in file.name for x in ['_202', 'daily_update', 'alert_digest']):
                modified = datetime.fromtimestamp(file.stat().st_mtime)
                if datetime.now() - modified > timedelta(days=30):
                    cleanup_candidates['old_reports'].append(file)
            
            # Temporary outputs
            if file.suffix == '.json' and 'progress' in file.name:
                cleanup_candidates['temp_outputs'].append(file)
    
    # Scan for cache
    for cache_dir in project_root.rglob('__pycache__'):
        cleanup_candidates['cache_files'].append(cache_dir)
    
    for pyc in project_root.rglob('*.pyc'):
        cleanup_candidates['cache_files'].append(pyc)
    
    # Report
    print("=" * 70)
    print("PROJECT CLEANUP REPORT")
    print("=" * 70)
    
    total = sum(len(v) for v in cleanup_candidates.values())
    
    if total == 0:
        print("\n✅ Project is clean! No files to remove.")
        return
    
    print(f"\nFound {total} files/directories to review:\n")
    
    for category, files in cleanup_candidates.items():
        if files:
            print(f"\n{category.upper().replace('_', ' ')} ({len(files)}):")
            for f in files[:10]:  # Show first 10
                print(f"  - {f.relative_to(project_root)}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")
    
    print("\n" + "=" * 70)
    print("ACTIONS")
    print("=" * 70)
    
    response = input("\nDelete all these files? (yes/no): ")
    
    if response.lower() == 'yes':
        deleted = 0
        for files in cleanup_candidates.values():
            for f in files:
                try:
                    if f.is_dir():
                        import shutil
                        shutil.rmtree(f)
                    else:
                        f.unlink()
                    deleted += 1
                except Exception as e:
                    print(f"  Error deleting {f}: {e}")
        
        print(f"\n✅ Deleted {deleted} files/directories")
    else:
        print("\n Cancelled - no files deleted")

if __name__ == "__main__":
    scan_for_cleanup()
```

---

## Code Audit Script

Create `src/scripts/audit_codebase.py`:
```python
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
```

---

## Recommended Maintenance Schedule

### Weekly
- Delete files in root directory >7 days old
- Check for failed scraper runs

### Monthly
- Run `cleanup_project.py`
- Run `audit_codebase.py`
- Archive old reports to `archive/` directory
- Review and consolidate similar scripts

### Quarterly
- Review all scripts in `src/scripts/`
- Remove unused functionality
- Update documentation
- Regenerate final system report

---

## Core Files to NEVER Delete
```
src/analytics/role_classifier.py
src/analytics/regression_detector.py
src/analytics/league_baselines.py
src/analytics/trend_tracker.py
src/analytics/predictive_model.py
src/analytics/player_report.py
src/automation/daily_scraper.py
src/automation/alert_digest.py
src/database/schema.sql
src/database/insert_data.py
src/scrapers/fangraphs.py
src/scrapers/batch_scraper.py
src/utils/db_connection.py
src/data/verified_players.py
requirements.txt
.env
README.md
```

---

## Git Ignore Recommendations

Add to `.gitignore`:
```
# Python
__pycache__/
*.pyc
*.pyo

# Project outputs
*.html
daily_update_*.json
alert_digest_*.txt
*_progress.json
*.log

# Environment
.env
venv/
.vscode/

# Archives
archive/

# System
.DS_Store
Thumbs.db
```