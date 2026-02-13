"""
Statcast Data Integration using pybaseball

Fetches and aggregates Statcast metrics for player-seasons:
- Exit velocity, launch angle, barrel rate
- Hard-hit%, sweet spot%
- Expected stats (xBA, xSLG, xwOBA)
- Advanced contact quality metrics
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pybaseball import statcast_batter, playerid_lookup, cache
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.db_connection import get_session
from sqlalchemy import text

cache.enable()


class StatcastScraper:
    """
    Scrape and aggregate Statcast data for players
    """
    
    def __init__(self):
        self.session = get_session()
    
    def get_mlbam_id_mapping(self):
        """
        Get mapping of FanGraphs IDs to MLB AM IDs
        
        Returns:
            Dict mapping fg_id -> mlbam_id
        """
        query = text("""
            SELECT p.fg_id, p.name, p.player_id
            FROM players p
            WHERE p.fg_id IS NOT NULL
        """)
        
        result = self.session.execute(query)
        players = result.fetchall()
        
        mapping = {}
        
        print(f"🔍 Looking up MLB AM IDs for {len(players)} players...")
        
        for fg_id, name, player_id in players:
            # Split name
            parts = name.split(' ', 1)
            if len(parts) != 2:
                continue
            
            first_name, last_name = parts
            
            try:
                # Use pybaseball to find IDs
                lookup = playerid_lookup(last_name, first_name)
                
                if lookup is not None and not lookup.empty:
                    # Take first match
                    mlbam_id = lookup.iloc[0]['key_mlbam']
                    
                    if pd.notna(mlbam_id):
                        mapping[fg_id] = {
                            'mlbam_id': int(mlbam_id),
                            'player_id': player_id,
                            'name': name
                        }
            except Exception as e:
                # Silently skip errors during bulk lookup
                pass
        
        print(f"✅ Mapped {len(mapping)}/{len(players)} players to MLB AM IDs")
        return mapping
    
    def fetch_statcast_season(self, mlbam_id, season, player_name="Player"):
        """
        Fetch Statcast data for a player-season
        
        Args:
            mlbam_id: MLB Advanced Media ID
            season: Season year
            player_name: Player name (for logging)
        
        Returns:
            DataFrame with raw Statcast data, or None if no data
        """
        start_date = f"{season}-03-01"
        end_date = f"{season}-11-30"
        
        try:
            print(f"   Fetching {season} Statcast data...", end=' ')
            
            data = statcast_batter(start_date, end_date, mlbam_id)
            
            if data is None or data.empty:
                print("No data")
                return None
            
            print(f"✅ {len(data)} batted balls")
            return data
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def aggregate_statcast_metrics(self, statcast_df):
        """
        Aggregate raw Statcast data to season-level metrics
        
        Args:
            statcast_df: Raw Statcast DataFrame
        
        Returns:
            Dict with aggregated metrics
        """
        if statcast_df is None or statcast_df.empty:
            return None
        
        # Filter to batted balls only
        batted_balls = statcast_df[statcast_df['type'].isin(['X'])]  # X = batted ball
        
        if batted_balls.empty:
            return None
        
        # Calculate aggregated metrics
        metrics = {}
        
        # Exit velocity
        if 'launch_speed' in batted_balls.columns:
            valid_ev = batted_balls['launch_speed'].dropna()
            if not valid_ev.empty:
                metrics['exit_velo'] = valid_ev.mean()
                metrics['max_exit_velo'] = valid_ev.max()
                metrics['ev_90th_percentile'] = valid_ev.quantile(0.9)
        
        # Launch angle
        if 'launch_angle' in batted_balls.columns:
            valid_la = batted_balls['launch_angle'].dropna()
            if not valid_la.empty:
                metrics['launch_angle'] = valid_la.mean()
        
        # Barrel rate (requires both EV and LA)
        if 'barrel' in batted_balls.columns:
            barrel_count = (batted_balls['barrel'] == 1).sum()
            metrics['barrel_pct'] = (barrel_count / len(batted_balls)) * 100
        
        # Hard-hit rate (95+ mph)
        if 'launch_speed' in batted_balls.columns:
            hard_hit_count = (batted_balls['launch_speed'] >= 95).sum()
            metrics['hard_hit_pct'] = (hard_hit_count / len(batted_balls)) * 100
        
        # Sweet spot rate (8-32 degrees launch angle)
        if 'launch_angle' in batted_balls.columns:
            sweet_spot_count = ((batted_balls['launch_angle'] >= 8) & 
                               (batted_balls['launch_angle'] <= 32)).sum()
            metrics['sweet_spot_pct'] = (sweet_spot_count / len(batted_balls)) * 100
        
        # Expected stats (xBA, xSLG, xwOBA)
        for xstat in ['estimated_ba_using_speedangle', 
                     'estimated_slg_using_speedangle',
                     'estimated_woba_using_speedangle']:
            if xstat in batted_balls.columns:
                valid = batted_balls[xstat].dropna()
                if not valid.empty:
                    # Map to shorter names
                    short_name = {
                        'estimated_ba_using_speedangle': 'xba',
                        'estimated_slg_using_speedangle': 'xslg',
                        'estimated_woba_using_speedangle': 'xwoba'
                    }[xstat]
                    metrics[short_name] = valid.mean()
        
        # Batted ball distribution
        if 'launch_speed' in batted_balls.columns and 'launch_angle' in batted_balls.columns:
            valid_bb = batted_balls.dropna(subset=['launch_speed', 'launch_angle'])
            
            if not valid_bb.empty:
                # Ground balls (<10 degrees)
                gb_count = (valid_bb['launch_angle'] < 10).sum()
                metrics['gb_pct_statcast'] = (gb_count / len(valid_bb)) * 100
                
                # Line drives (10-25 degrees)
                ld_count = ((valid_bb['launch_angle'] >= 10) & 
                           (valid_bb['launch_angle'] <= 25)).sum()
                metrics['ld_pct_statcast'] = (ld_count / len(valid_bb)) * 100
                
                # Fly balls (25-50 degrees)
                fb_count = ((valid_bb['launch_angle'] > 25) & 
                           (valid_bb['launch_angle'] <= 50)).sum()
                metrics['fb_pct_statcast'] = (fb_count / len(valid_bb)) * 100
                
                # Pop-ups (>50 degrees)
                pu_count = (valid_bb['launch_angle'] > 50).sum()
                metrics['pu_pct_statcast'] = (pu_count / len(valid_bb)) * 100
        
        # Sample size
        metrics['batted_balls'] = len(batted_balls)
        
        return metrics
    
    def insert_statcast_data(self, player_id, season, metrics):
        """
        Insert or update Statcast data in database
        
        Args:
            player_id: Database player_id
            season: Season year
            metrics: Dict of Statcast metrics
        """
        try:
            # Build insert query
            columns = ['player_id', 'season'] + list(metrics.keys())
            values = [player_id, season] + list(metrics.values())
            
            # Create placeholders
            placeholders = ', '.join([f':{col}' for col in columns])
            columns_str = ', '.join(columns)
            
            # Create update clause (for conflict resolution)
            update_clause = ', '.join([f'{col} = EXCLUDED.{col}' 
                                      for col in metrics.keys()])
            
            query = text(f"""
                INSERT INTO statcast_data ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT (player_id, season)
                DO UPDATE SET
                    {update_clause},
                    uploaded_at = CURRENT_TIMESTAMP
            """)
            
            # Create params dict
            params = {col: val for col, val in zip(columns, values)}
            
            self.session.execute(query, params)
            self.session.commit()
            
            print(f"   ✅ Inserted Statcast data")
            
        except Exception as e:
            self.session.rollback()
            print(f"   ❌ Database error: {e}")
    
    def scrape_player_statcast(self, fg_id, mlbam_id, player_id, player_name, 
                               seasons=[2020, 2021, 2022, 2023, 2024, 2025]):
        """
        Scrape Statcast data for a player across multiple seasons
        
        Args:
            fg_id: FanGraphs ID
            mlbam_id: MLB AM ID
            player_id: Database player_id
            player_name: Player name
            seasons: List of seasons to fetch
        
        Returns:
            Number of seasons successfully loaded
        """
        print(f"\n{player_name} (FG: {fg_id}, MLBAM: {mlbam_id})")
        
        loaded = 0
        
        for season in seasons:
            # Fetch raw data
            statcast_df = self.fetch_statcast_season(mlbam_id, season, player_name)
            
            if statcast_df is not None:
                # Aggregate metrics
                metrics = self.aggregate_statcast_metrics(statcast_df)
                
                if metrics:
                    # Insert to database
                    self.insert_statcast_data(player_id, season, metrics)
                    loaded += 1
        
        return loaded
    
    def scrape_all_players(self, seasons=[2020, 2021, 2022, 2023, 2024, 2025]):
        """
        Scrape Statcast data for all players in database
        
        Args:
            seasons: List of seasons to fetch
        """
        print("=" * 70)
        print("STATCAST DATA SCRAPER")
        print("=" * 70)
        print(f"\nSeasons: {', '.join(map(str, seasons))}")
        
        # Get ID mapping
        mapping = self.get_mlbam_id_mapping()
        
        if not mapping:
            print("❌ No players found with MLB AM IDs")
            return
        
        print(f"\n📊 Will fetch Statcast data for {len(mapping)} players")
        print(f"   Estimated time: ~{len(mapping) * len(seasons) * 3 / 60:.0f} minutes")
        print()
        
        response = input("Proceed? (yes/no): ").strip().lower()
        
        if response != 'yes' and response != 'y':
            print("Cancelled.")
            return
        
        # Scrape each player
        print("\n" + "=" * 70)
        print("FETCHING STATCAST DATA")
        print("=" * 70)
        
        successful = 0
        failed = 0
        total_seasons = 0
        
        for i, (fg_id, info) in enumerate(mapping.items(), 1):
            print(f"\n[{i}/{len(mapping)}]", end=' ')
            
            seasons_loaded = self.scrape_player_statcast(
                fg_id, 
                info['mlbam_id'],
                info['player_id'],
                info['name'],
                seasons
            )
            
            if seasons_loaded > 0:
                successful += 1
                total_seasons += seasons_loaded
            else:
                failed += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("STATCAST SCRAPING COMPLETE")
        print("=" * 70)
        
        print(f"\n📊 Summary:")
        print(f"   Players processed: {len(mapping)}")
        print(f"   ✅ With Statcast data: {successful}")
        print(f"   ❌ No Statcast data: {failed}")
        print(f"   Total seasons loaded: {total_seasons}")
        print(f"   Average seasons per player: {total_seasons/successful:.1f}")
    
    def close(self):
        """Close database session"""
        self.session.close()


def run_statcast_scraper():
    """
    Interactive Statcast scraper
    """
    print("=" * 70)
    print("STATCAST DATA INTEGRATION")
    print("=" * 70)
    print()
    print("This will fetch Statcast data for all players in the database.")
    print("Statcast data includes:")
    print("  - Exit velocity, launch angle")
    print("  - Barrel%, hard-hit%")
    print("  - Expected stats (xBA, xSLG, xwOBA)")
    print("  - Batted ball distributions")
    print()
    print("Note: Statcast data is only available from 2015 onwards,")
    print("but quality significantly improved from 2020+.")
    print()
    
    # Get season range
    default_seasons = [2020, 2021, 2022, 2023, 2024, 2025]
    print(f"Default seasons: {', '.join(map(str, default_seasons))}")
    print()
    
    response = input("Use default seasons? (yes/no): ").strip().lower()
    
    if response == 'yes' or response == 'y':
        seasons = default_seasons
    else:
        seasons_input = input("Enter seasons (comma-separated, e.g. 2020,2021,2022): ").strip()
        seasons = [int(s.strip()) for s in seasons_input.split(',')]
    
    # Run scraper
    scraper = StatcastScraper()
    
    try:
        scraper.scrape_all_players(seasons)
    finally:
        scraper.close()


if __name__ == "__main__":
    run_statcast_scraper()
