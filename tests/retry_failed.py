import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.batch_scraper import scrape_multiple_players

# Just the failed players
failed_players = [
    ("Paul Goldschmidt", "8973"),
    ("Ketel Marte", "11908"),
    ("Ronald Acuna Jr.", "18401"),
    ("Corbin Carroll", "26138"),
]

print("🔄 Retrying failed players...")
results = scrape_multiple_players(failed_players, start_year=2015, end_year=2025, delay=2)
print(f"\n✅ Retry complete! {len(results['success'])}/4 now loaded")