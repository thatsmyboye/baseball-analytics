"""
Add birth dates to players using known data
"""
import sys
from pathlib import Path
from datetime import date

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.db_connection import get_session
from sqlalchemy import text

# Known birth dates for our players
BIRTH_DATES = {
    "Harrison Bader": date(1994, 6, 3),
    "Aaron Judge": date(1992, 4, 26),
    "Shohei Ohtani": date(1994, 7, 5),
    "Mike Trout": date(1991, 8, 7),
    "Juan Soto": date(1998, 10, 25),
    "Mookie Betts": date(1992, 10, 7),
    "Ronald Acuna Jr.": date(1997, 12, 18),
    "Vladimir Guerrero Jr.": date(1999, 3, 16),
    "Bobby Witt Jr.": date(2000, 6, 14),
    "Julio Rodriguez": date(2000, 12, 29),
    "Freddie Freeman": date(1989, 9, 12),
    "Paul Goldschmidt": date(1987, 9, 10),
    "Nolan Arenado": date(1991, 4, 16),
    "Jose Ramirez": date(1992, 9, 17),
    "Rafael Devers": date(1996, 10, 24),
    "Matt Olson": date(1994, 3, 29),
    "Pete Alonso": date(1994, 12, 7),
    "Francisco Lindor": date(1993, 11, 14),
    "Trea Turner": date(1993, 6, 30),
    "Corey Seager": date(1994, 4, 27),
    "Marcus Semien": date(1990, 9, 17),
    "Jose Altuve": date(1990, 5, 6),
    "Ozzie Albies": date(1997, 1, 7),
    "Gleyber Torres": date(1996, 12, 13),
    "Kyle Tucker": date(1997, 1, 17),
    "Randy Arozarena": date(1995, 2, 28),
    "Yordan Alvarez": date(1997, 6, 27),
    "Fernando Tatis Jr.": date(1999, 1, 2),
    "Corbin Carroll": date(2000, 8, 21),
    "George Springer": date(1989, 9, 19),
    "Giancarlo Stanton": date(1989, 11, 8),
    "Christian Yelich": date(1991, 12, 5),
    "Bryan Reynolds": date(1995, 1, 27),
    "Ketel Marte": date(1993, 10, 12),
    "Jazz Chisholm Jr.": date(1998, 2, 1),
    "Dansby Swanson": date(1994, 2, 11),
    "Austin Riley": date(1997, 4, 2),
    "Will Smith": date(1995, 3, 28),
    "J.T. Realmuto": date(1991, 3, 18),
    "Salvador Perez": date(1990, 5, 10),
    "Adley Rutschman": date(1998, 2, 6),
    "Cal Raleigh": date(1996, 11, 26),
    "Kyle Schwarber": date(1993, 3, 5),
    "Anthony Santander": date(1994, 10, 19),
    "Teoscar Hernandez": date(1992, 10, 15),
    "Ian Happ": date(1994, 8, 12),
    "Cedric Mullins": date(1994, 10, 1),
    "Jesse Winker": date(1993, 8, 17),
    "Michael Harris II": date(2001, 3, 9),
    "Steven Kwan": date(1997, 9, 5),
    "Kris Bryant": date(1992, 1, 4),
}

def add_birth_dates():
    """Add birth dates to players table"""
    session = get_session()
    
    try:
        updated = 0
        not_found = []
        
        for player_name, birth_date in BIRTH_DATES.items():
            # Check if player exists
            result = session.execute(
                text("SELECT player_id FROM players WHERE name = :name"),
                {'name': player_name}
            ).fetchone()
            
            if result:
                # Update birth date
                session.execute(
                    text("UPDATE players SET birth_date = :birth_date WHERE player_id = :player_id"),
                    {'birth_date': birth_date, 'player_id': result[0]}
                )
                updated += 1
                print(f"✅ Updated {player_name}: {birth_date}")
            else:
                not_found.append(player_name)
                print(f"⚠️  Player not found: {player_name}")
        
        session.commit()
        
        print(f"\n📊 Summary:")
        print(f"   Updated: {updated}")
        print(f"   Not found: {len(not_found)}")
        
        if not_found:
            print(f"\n   Missing players:")
            for name in not_found:
                print(f"      - {name}")
    
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 70)
    print("ADD BIRTH DATES TO PLAYERS")
    print("=" * 70)
    
    add_birth_dates()