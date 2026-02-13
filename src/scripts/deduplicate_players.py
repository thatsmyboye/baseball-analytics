"""
Deduplicate players table and consolidate stats
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.db_connection import get_session
from sqlalchemy import text

def deduplicate_players():
    """
    Find duplicate players and consolidate them
    Keep the one with birth_date, merge all stats to that ID
    """
    session = get_session()
    
    try:
        # Find duplicates
        duplicates = session.execute(
            text("""
                SELECT name, COUNT(*) as count, 
                       STRING_AGG(player_id::text, ',' ORDER BY player_id) as ids
                FROM players
                GROUP BY name
                HAVING COUNT(*) > 1
                ORDER BY name
            """)
        ).fetchall()
        
        print(f"Found {len(duplicates)} duplicate player names\n")
        
        for name, count, ids in duplicates:
            id_list = [int(i) for i in ids.split(',')]
            
            print(f"Processing: {name} ({count} duplicates)")
            print(f"   Player IDs: {id_list}")
            
            # Find which ID has birth_date
            id_with_birthdate = None
            for pid in id_list:
                result = session.execute(
                    text("SELECT birth_date FROM players WHERE player_id = :pid"),
                    {'pid': pid}
                ).fetchone()
                
                if result[0]:
                    id_with_birthdate = pid
                    break
            
            # If none have birth_date, keep the lowest ID
            keep_id = id_with_birthdate if id_with_birthdate else min(id_list)
            delete_ids = [i for i in id_list if i != keep_id]
            
            print(f"   Keeping ID: {keep_id}")
            print(f"   Deleting IDs: {delete_ids}")
            
            # Reassign all season_stats to the kept ID
            for delete_id in delete_ids:
                # Check for conflicting season/team combinations
                conflicts = session.execute(
                    text("""
                        SELECT s1.season, s1.team
                        FROM season_stats s1
                        WHERE s1.player_id = :delete_id
                        AND EXISTS (
                            SELECT 1 FROM season_stats s2
                            WHERE s2.player_id = :keep_id
                            AND s2.season = s1.season
                            AND s2.team = s1.team
                        )
                    """),
                    {'delete_id': delete_id, 'keep_id': keep_id}
                ).fetchall()
                
                if conflicts:
                    print(f"      Found {len(conflicts)} conflicting season/team records, deleting duplicates")
                    # Delete the duplicate records from the ID we're removing
                    for season, team in conflicts:
                        session.execute(
                            text("""
                                DELETE FROM season_stats 
                                WHERE player_id = :delete_id 
                                AND season = :season 
                                AND team = :team
                            """),
                            {'delete_id': delete_id, 'season': season, 'team': team}
                        )
                
                # Update remaining records to kept ID
                updated = session.execute(
                    text("""
                        UPDATE season_stats 
                        SET player_id = :keep_id 
                        WHERE player_id = :delete_id
                    """),
                    {'keep_id': keep_id, 'delete_id': delete_id}
                )
                print(f"      Reassigned {updated.rowcount} season records from ID {delete_id}")
            
            # Delete the duplicate player records
            for delete_id in delete_ids:
                session.execute(
                    text("DELETE FROM players WHERE player_id = :pid"),
                    {'pid': delete_id}
                )
            
            print(f"   ✅ Consolidated {name}\n")
        
        session.commit()
        
        # Verify
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        
        remaining_duplicates = session.execute(
            text("""
                SELECT name, COUNT(*) as count
                FROM players
                GROUP BY name
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        
        if remaining_duplicates:
            print(f"⚠️  Still {len(remaining_duplicates)} duplicates remaining:")
            for name, count in remaining_duplicates:
                print(f"   - {name}: {count}")
        else:
            print("✅ No duplicates remaining!")
        
        total_players = session.execute(text("SELECT COUNT(*) FROM players")).fetchone()[0]
        total_seasons = session.execute(text("SELECT COUNT(*) FROM season_stats")).fetchone()[0]
        
        print(f"\n📊 Final counts:")
        print(f"   Total players: {total_players}")
        print(f"   Total season records: {total_seasons}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 70)
    print("DEDUPLICATE PLAYERS TABLE")
    print("=" * 70)
    print()
    
    response = input("This will modify the database. Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        deduplicate_players()
    else:
        print("Cancelled.")