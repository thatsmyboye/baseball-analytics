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