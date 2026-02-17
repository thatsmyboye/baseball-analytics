"""
Update Razzball Player ID Mapping

Fetches the latest MLBAM ID table from https://razzball.com/mlbamids/,
compares it against the local CSV, reports deltas, and updates the file.

Usage:
    python src/scripts/update_razzball_ids.py
    python src/scripts/update_razzball_ids.py --dry-run   # Preview changes only
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO

RAZZBALL_URL = "https://razzball.com/mlbamids/"
LOCAL_CSV = project_root / "src" / "data" / "razzball.csv"
BACKUP_DIR = project_root / "src" / "data" / "backups"

# Columns that define a unique player record
KEY_COLUMNS = ["MLBAMID", "Name"]
# Columns where changes are worth tracking
TRACKED_COLUMNS = [
    "MLBAMID", "RazzballID", "FanGraphsID", "NFBCID", "FantraxID",
    "Team", "STD_POS", "YAHOO_POS",
]


def fetch_razzball_html():
    """Fetch the MLBAMIDs page HTML from Razzball."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    resp = requests.get(RAZZBALL_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_table_from_html(html):
    """
    Extract the player ID table from the Razzball page HTML.

    Razzball uses a DataTable rendered as an HTML <table>.  We grab the
    first table that contains an 'MLBAMID' column header.
    """
    soup = BeautifulSoup(html, "lxml")

    # Look for tables containing the MLBAMID header
    for table in soup.find_all("table"):
        header_text = table.get_text()
        if "MLBAMID" in header_text:
            dfs = pd.read_html(StringIO(str(table)))
            if dfs:
                df = dfs[0]
                if "MLBAMID" in df.columns:
                    return df

    # Fallback: try all tables on the page
    dfs = pd.read_html(StringIO(html))
    for df in dfs:
        if "MLBAMID" in df.columns:
            return df

    raise ValueError(
        "Could not find a table with 'MLBAMID' column on the Razzball page. "
        "The page structure may have changed."
    )


def parse_last_updated(html):
    """Try to extract the 'last updated' timestamp from the page."""
    soup = BeautifulSoup(html, "lxml")
    for text_node in soup.stripped_strings:
        lower = text_node.lower()
        if "updated" in lower or "last" in lower:
            if any(month in lower for month in [
                "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec",
            ]):
                return text_node.strip()
    return None


def load_local_csv():
    """Load the existing local razzball.csv."""
    if not LOCAL_CSV.exists():
        print(f"No existing CSV found at {LOCAL_CSV}")
        return pd.DataFrame()
    return pd.read_csv(LOCAL_CSV, encoding="utf-8-sig")


def normalize_df(df):
    """Normalize a DataFrame for consistent comparison."""
    df = df.copy()
    # Ensure consistent column naming
    df.columns = df.columns.str.strip()
    # Fill NaN with empty string for comparison
    df = df.fillna("")
    # Convert all values to strings for comparison
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def compute_deltas(old_df, new_df):
    """
    Compare old and new DataFrames and return a summary of changes.

    Returns:
        dict with keys: added, removed, changed, unchanged_count
    """
    old_norm = normalize_df(old_df)
    new_norm = normalize_df(new_df)

    # Use MLBAMID as the primary key for matching
    old_by_id = {row["MLBAMID"]: row for _, row in old_norm.iterrows()}
    new_by_id = {row["MLBAMID"]: row for _, row in new_norm.iterrows()}

    old_ids = set(old_by_id.keys())
    new_ids = set(new_by_id.keys())

    added_ids = new_ids - old_ids
    removed_ids = old_ids - new_ids
    common_ids = old_ids & new_ids

    added = []
    for mid in sorted(added_ids):
        row = new_by_id[mid]
        added.append({
            "MLBAMID": mid,
            "Name": row.get("Name", ""),
            "Team": row.get("Team", ""),
            "Position": row.get("STD_POS", ""),
        })

    removed = []
    for mid in sorted(removed_ids):
        row = old_by_id[mid]
        removed.append({
            "MLBAMID": mid,
            "Name": row.get("Name", ""),
            "Team": row.get("Team", ""),
            "Position": row.get("STD_POS", ""),
        })

    changed = []
    unchanged_count = 0
    for mid in sorted(common_ids):
        old_row = old_by_id[mid]
        new_row = new_by_id[mid]
        diffs = {}
        for col in TRACKED_COLUMNS:
            if col in old_row.index and col in new_row.index:
                old_val = old_row[col]
                new_val = new_row[col]
                if old_val != new_val:
                    diffs[col] = {"old": old_val, "new": new_val}
        if diffs:
            changed.append({
                "MLBAMID": mid,
                "Name": new_row.get("Name", old_row.get("Name", "")),
                "changes": diffs,
            })
        else:
            unchanged_count += 1

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": unchanged_count,
    }


def print_delta_report(deltas, last_updated=None):
    """Print a human-readable delta report."""
    print("=" * 70)
    print("Razzball Player ID Update Report")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if last_updated:
        print(f"Razzball last updated: {last_updated}")
    print("=" * 70)

    added = deltas["added"]
    removed = deltas["removed"]
    changed = deltas["changed"]
    unchanged = deltas["unchanged_count"]

    print(f"\nSummary: {len(added)} added, {len(removed)} removed, "
          f"{len(changed)} changed, {unchanged} unchanged\n")

    if added:
        print(f"--- NEW PLAYERS ({len(added)}) ---")
        for p in added:
            print(f"  + {p['Name']} ({p['Team']}, {p['Position']}) "
                  f"[MLBAMID: {p['MLBAMID']}]")
        print()

    if removed:
        print(f"--- REMOVED PLAYERS ({len(removed)}) ---")
        for p in removed:
            print(f"  - {p['Name']} ({p['Team']}, {p['Position']}) "
                  f"[MLBAMID: {p['MLBAMID']}]")
        print()

    if changed:
        print(f"--- CHANGED PLAYERS ({len(changed)}) ---")
        for p in changed:
            print(f"  ~ {p['Name']} [MLBAMID: {p['MLBAMID']}]")
            for col, vals in p["changes"].items():
                print(f"      {col}: {vals['old']} -> {vals['new']}")
        print()

    if not added and not removed and not changed:
        print("No changes detected. Local CSV is up to date.\n")


def backup_existing_csv():
    """Create a timestamped backup of the current CSV."""
    if not LOCAL_CSV.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"razzball_{timestamp}.csv"
    import shutil
    shutil.copy2(LOCAL_CSV, backup_path)
    return backup_path


def main():
    parser = argparse.ArgumentParser(
        description="Update Razzball player ID mapping from razzball.com/mlbamids/"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without updating the local CSV",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup of the existing CSV",
    )
    args = parser.parse_args()

    # Step 1: Fetch latest data
    print("Fetching latest player IDs from Razzball...")
    try:
        html = fetch_razzball_html()
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch Razzball page: {e}")
        sys.exit(1)

    last_updated = parse_last_updated(html)
    if last_updated:
        print(f"Razzball page last updated: {last_updated}")

    # Step 2: Parse the table
    print("Parsing player ID table...")
    try:
        new_df = parse_table_from_html(html)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    print(f"Found {len(new_df)} players in remote table")

    # Step 3: Load local data
    old_df = load_local_csv()
    if old_df.empty:
        print("No existing local CSV found. Will create a new one.")
    else:
        print(f"Loaded {len(old_df)} players from local CSV")

    # Step 4: Compute and report deltas
    if not old_df.empty:
        deltas = compute_deltas(old_df, new_df)
        print_delta_report(deltas, last_updated)

        has_changes = (
            deltas["added"] or deltas["removed"] or deltas["changed"]
        )
    else:
        has_changes = True
        print("Creating new local CSV from remote data.\n")

    # Step 5: Update local file
    if has_changes and not args.dry_run:
        if not args.no_backup and not old_df.empty:
            backup_path = backup_existing_csv()
            if backup_path:
                print(f"Backup saved to: {backup_path}")

        new_df.to_csv(LOCAL_CSV, index=False, encoding="utf-8-sig")
        print(f"Updated {LOCAL_CSV} with {len(new_df)} players")
    elif args.dry_run and has_changes:
        print("[DRY RUN] No files were modified.")
    elif not has_changes:
        print("No update needed.")


if __name__ == "__main__":
    main()
