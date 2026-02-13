"""
Check what player names are actually in the database
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.db_connection import get_session
from sqlalchemy import text

def check_names():
    """List all players without birth dates"""
    session = get_session()
    
    try:
        result = session.execute(
            text("""
                SELECT player_id, name, birth_date
                FROM players
                ORDER BY name
            """)
        ).fetchall()
        
        print("All players in database:")
        print("-" * 70)
        
        with_birthdate = 0
        without_birthdate = []
        
        for player_id, name, birth_date in result:
            if birth_date:
                print(f"✅ {name} (ID: {player_id}) - {birth_date}")
                with_birthdate += 1
            else:
                print(f"❌ {name} (ID: {player_id}) - NO BIRTH DATE")
                without_birthdate.append(name)
        
        print(f"\n📊 Summary:")
        print(f"   With birth date: {with_birthdate}")
        print(f"   Without birth date: {len(without_birthdate)}")
        
        if without_birthdate:
            print(f"\n   Names without birth dates:")
            for name in without_birthdate:
                print(f"      '{name}'")
    
    finally:
        session.close()

if __name__ == "__main__":
    check_names()