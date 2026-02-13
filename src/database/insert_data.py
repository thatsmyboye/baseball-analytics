import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.utils.db_connection import get_session, engine
import pandas as pd

def insert_or_update_player(name, fg_id=None, bbref_id=None):
    """
    Insert a new player or update existing player record
    
    Args:
        name: Player's full name
        fg_id: FanGraphs player ID
        bbref_id: Baseball Reference player ID
    
    Returns:
        player_id: The database player_id
    """
    session = get_session()
    
    try:
        # Check if player already exists (by fg_id or name)
        if fg_id:
            result = session.execute(
                text("SELECT player_id FROM players WHERE fg_id = :fg_id"),
                {"fg_id": fg_id}
            ).fetchone()
        else:
            result = session.execute(
                text("SELECT player_id FROM players WHERE name = :name"),
                {"name": name}
            ).fetchone()
        
        if result:
            # Player exists, return their ID
            player_id = result[0]
            print(f"   Found existing player: {name} (ID: {player_id})")
            
            # Update FG ID if it was missing
            if fg_id and not result:
                session.execute(
                    text("UPDATE players SET fg_id = :fg_id WHERE player_id = :player_id"),
                    {"fg_id": fg_id, "player_id": player_id}
                )
                session.commit()
                print(f"   Updated FanGraphs ID for {name}")
            
            return player_id
        else:
            # Insert new player
            result = session.execute(
                text("""
                    INSERT INTO players (name, fg_id, bbref_id)
                    VALUES (:name, :fg_id, :bbref_id)
                    RETURNING player_id
                """),
                {"name": name, "fg_id": fg_id, "bbref_id": bbref_id}
            )
            session.commit()
            player_id = result.fetchone()[0]
            print(f"   Created new player: {name} (ID: {player_id})")
            return player_id
            
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error inserting/updating player: {e}")
        raise
    finally:
        session.close()


def insert_season_stats(player_id, stats_df):
    """
    Insert or update season stats for a player
    
    Args:
        player_id: Database player_id
        stats_df: DataFrame with parsed season stats (from parse_fangraphs_columns)
    
    Returns:
        Number of rows inserted/updated
    """
    session = get_session()
    
    try:
        inserted_count = 0
        updated_count = 0
        
        for _, row in stats_df.iterrows():
            season = int(row['season']) if pd.notna(row['season']) else None
            team = row['team'] if pd.notna(row['team']) else None
            
            if not season:
                print(f"   ⚠️  Skipping row with no season")
                continue
            
            # Check if this season already exists for this player
            existing = session.execute(
                text("""
                    SELECT id FROM season_stats 
                    WHERE player_id = :player_id AND season = :season AND team = :team
                """),
                {"player_id": player_id, "season": season, "team": team}
            ).fetchone()
            
            # Prepare data for insertion
            data = {
                'player_id': player_id,
                'season': season,
                'team': team,
                'games': int(row['games']) if pd.notna(row['games']) else None,
                'pa': int(row['pa']) if pd.notna(row['pa']) else None,
                'ab': int(row['ab']) if pd.notna(row['ab']) else None,
                'hits': int(row['hits']) if pd.notna(row['hits']) else None,
                'doubles': int(row['doubles']) if pd.notna(row['doubles']) else None,
                'triples': int(row['triples']) if pd.notna(row['triples']) else None,
                'hr': int(row['hr']) if pd.notna(row['hr']) else None,
                'rbi': int(row['rbi']) if pd.notna(row['rbi']) else None,
                'bb': int(row['bb']) if pd.notna(row['bb']) else None,
                'so': int(row['so']) if pd.notna(row['so']) else None,
                'avg': float(row['avg']) if pd.notna(row['avg']) else None,
                'obp': float(row['obp']) if pd.notna(row['obp']) else None,
                'slg': float(row['slg']) if pd.notna(row['slg']) else None,
                'woba': float(row['woba']) if pd.notna(row['woba']) else None,
                'wrc_plus': int(row['wrc_plus']) if pd.notna(row['wrc_plus']) else None,
                'babip': float(row['babip']) if pd.notna(row['babip']) else None,
                'bb_pct': float(row['bb_pct']) if pd.notna(row['bb_pct']) else None,
                'k_pct': float(row['k_pct']) if pd.notna(row['k_pct']) else None,
                'iso': float(row['iso']) if pd.notna(row['iso']) else None,
                'gb_pct': float(row['gb_pct']) if pd.notna(row['gb_pct']) else None,
                'fb_pct': float(row['fb_pct']) if pd.notna(row['fb_pct']) else None,
                'ld_pct': float(row['ld_pct']) if pd.notna(row['ld_pct']) else None,
                'hr_fb_pct': float(row['hr_fb_pct']) if pd.notna(row['hr_fb_pct']) else None,
            }
            
            if existing:
                # Update existing record
                session.execute(
                    text("""
                        UPDATE season_stats SET
                            games = :games, pa = :pa, ab = :ab, hits = :hits,
                            doubles = :doubles, triples = :triples, hr = :hr,
                            rbi = :rbi, bb = :bb, so = :so,
                            avg = :avg, obp = :obp, slg = :slg, woba = :woba,
                            wrc_plus = :wrc_plus, babip = :babip,
                            bb_pct = :bb_pct, k_pct = :k_pct, iso = :iso,
                            gb_pct = :gb_pct, fb_pct = :fb_pct, ld_pct = :ld_pct,
                            hr_fb_pct = :hr_fb_pct,
                            scraped_at = CURRENT_TIMESTAMP
                        WHERE player_id = :player_id AND season = :season AND team = :team
                    """),
                    data
                )
                updated_count += 1
            else:
                # Insert new record
                session.execute(
                    text("""
                        INSERT INTO season_stats (
                            player_id, season, team, games, pa, ab, hits,
                            doubles, triples, hr, rbi, bb, so,
                            avg, obp, slg, woba, wrc_plus, babip,
                            bb_pct, k_pct, iso, gb_pct, fb_pct, ld_pct, hr_fb_pct
                        ) VALUES (
                            :player_id, :season, :team, :games, :pa, :ab, :hits,
                            :doubles, :triples, :hr, :rbi, :bb, :so,
                            :avg, :obp, :slg, :woba, :wrc_plus, :babip,
                            :bb_pct, :k_pct, :iso, :gb_pct, :fb_pct, :ld_pct, :hr_fb_pct
                        )
                    """),
                    data
                )
                inserted_count += 1
        
        session.commit()
        print(f"   ✅ Inserted {inserted_count} new seasons, updated {updated_count} existing seasons")
        return inserted_count + updated_count
        
    except Exception as e:
        session.rollback()
        print(f"   ❌ Error inserting season stats: {e}")
        raise
    finally:
        session.close()


def load_player_to_database(player_name, fg_id, stats_df):
    """
    Complete workflow: Insert player and their season stats
    
    Args:
        player_name: Player's full name
        fg_id: FanGraphs player ID
        stats_df: Parsed DataFrame from FanGraphs scraper
    
    Returns:
        player_id
    """
    print(f"\n💾 Loading {player_name} to database...")
    
    # Step 1: Insert/update player
    player_id = insert_or_update_player(player_name, fg_id=fg_id)
    
    # Step 2: Insert season stats
    insert_season_stats(player_id, stats_df)
    
    print(f"✅ Successfully loaded {player_name} (player_id: {player_id})")
    return player_id


if __name__ == "__main__":
    # Test with Harrison Bader
    from src.scrapers.fangraphs import scrape_player_season_stats, parse_fangraphs_columns
    
    print("=" * 60)
    print("Testing Database Insertion - Harrison Bader")
    print("=" * 60)
    
    # Scrape data
    data = scrape_player_season_stats("Harrison Bader", 2015, 2025)
    
    if data is not None:
        # Parse to database format
        cleaned = parse_fangraphs_columns(data)
        
        # Load to database
        player_id = load_player_to_database("Harrison Bader", "18030", cleaned)
        
        print(f"\n🎉 Test complete! Harrison Bader loaded with player_id: {player_id}")