"""
League Baselines and Percentile Calculator

Calculate:
- League-wide percentiles for key metrics
- Role-based cohort comparisons
- Historical context
"""
import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db_connection import get_session

class LeagueBaselines:
    """
    Calculate league baselines and percentiles
    """
    
    def __init__(self):
        self.percentiles = [10, 25, 50, 75, 90]
    
    def calculate_league_percentiles(self, season=2025, min_pa=100):
        """
        Calculate league percentiles for all key metrics
        
        Returns:
            DataFrame with percentile breakdowns
        """
        session = get_session()
        
        try:
            query = text("""
                SELECT 
                    avg, obp, slg, woba, wrc_plus, babip,
                    bb_pct, k_pct, iso, hr_fb_pct
                FROM season_stats
                WHERE season = :season
                  AND pa >= :min_pa
                  AND avg IS NOT NULL
            """)
            
            df = pd.read_sql(query, session.bind, params={'season': season, 'min_pa': min_pa})
            
            if df.empty:
                return None
            
            # Calculate percentiles for each metric
            metrics = ['avg', 'obp', 'slg', 'woba', 'wrc_plus', 'babip', 
                      'bb_pct', 'k_pct', 'iso', 'hr_fb_pct']
            
            percentile_data = {}
            
            for metric in metrics:
                if metric in df.columns:
                    percentile_data[metric] = {
                        f'p{p}': df[metric].quantile(p/100) 
                        for p in self.percentiles
                    }
                    percentile_data[metric]['mean'] = df[metric].mean()
                    percentile_data[metric]['std'] = df[metric].std()
            
            return percentile_data
        
        finally:
            session.close()
    
    def get_player_percentile(self, value, metric, season=2025, min_pa=100):
        """
        Get a player's percentile rank for a specific metric
        
        Returns:
            int (0-100 percentile)
        """
        session = get_session()
        
        try:
            query = text(f"""
                SELECT {metric}
                FROM season_stats
                WHERE season = :season
                  AND pa >= :min_pa
                  AND {metric} IS NOT NULL
                ORDER BY {metric}
            """)
            
            df = pd.read_sql(query, session.bind, params={'season': season, 'min_pa': min_pa})
            
            if df.empty or value is None:
                return None
            
            # Calculate percentile
            percentile = (df[metric] < value).sum() / len(df) * 100
            
            return round(percentile)
        
        finally:
            session.close()
    
    def calculate_role_cohort_stats(self, season=2025, min_pa=100):
        """
        Calculate statistics by role cohort
        
        Returns:
            DataFrame with role-based averages
        """
        from src.analytics.role_classifier import RoleClassifier
        
        classifier = RoleClassifier()
        classifications = classifier.classify_all_seasons()
        
        if classifications.empty:
            return None
        
        # Filter for target season
        season_data = classifications[classifications['season'] == season]
        
        if season_data.empty:
            return None
        
        # Get stats for these players
        session = get_session()
        
        try:
            # Join classifications with stats
            player_seasons = season_data[['player_id', 'role']].to_dict('records')
            
            cohort_stats = {}
            
            for role in season_data['role'].unique():
                role_players = season_data[season_data['role'] == role]['player_id'].tolist()
                
                if not role_players:
                    continue
                
                # Get stats for this role
                placeholders = ','.join([str(p) for p in role_players])
                query = f"""
                    SELECT 
                        AVG(wrc_plus) as avg_wrc_plus,
                        AVG(babip) as avg_babip,
                        AVG(bb_pct) as avg_bb_pct,
                        AVG(k_pct) as avg_k_pct,
                        AVG(iso) as avg_iso,
                        COUNT(*) as player_count
                    FROM season_stats
                    WHERE player_id IN ({placeholders})
                      AND season = :season
                      AND pa >= :min_pa
                """
                
                result = session.execute(
                    text(query),
                    {'season': season, 'min_pa': min_pa}
                ).fetchone()
                
                if result:
                    cohort_stats[role] = {
                        'avg_wrc_plus': result[0],
                        'avg_babip': result[1],
                        'avg_bb_pct': result[2],
                        'avg_k_pct': result[3],
                        'avg_iso': result[4],
                        'player_count': result[5]
                    }
            
            return cohort_stats
        
        finally:
            session.close()
    
    def compare_player_to_league(self, player_stats, season=2025, min_pa=100):
        """
        Compare a player's stats to league percentiles
        
        Returns:
            dict with percentile rankings
        """
        percentile_ranks = {}
        
        metrics_to_compare = {
            'wrc_plus': 'wRC+',
            'babip': 'BABIP',
            'bb_pct': 'BB%',
            'k_pct': 'K%',
            'iso': 'ISO',
            'avg': 'AVG',
            'obp': 'OBP',
            'slg': 'SLG'
        }
        
        for metric, display_name in metrics_to_compare.items():
            if metric in player_stats and player_stats[metric] is not None:
                percentile = self.get_player_percentile(
                    player_stats[metric], 
                    metric, 
                    season, 
                    min_pa
                )
                
                if percentile is not None:
                    percentile_ranks[display_name] = {
                        'value': player_stats[metric],
                        'percentile': percentile,
                        'tier': self._percentile_to_tier(percentile)
                    }
        
        return percentile_ranks
    
    def _percentile_to_tier(self, percentile):
        """Convert percentile to tier description"""
        if percentile >= 90:
            return 'Elite'
        elif percentile >= 75:
            return 'Above Average'
        elif percentile >= 50:
            return 'Average'
        elif percentile >= 25:
            return 'Below Average'
        else:
            return 'Poor'


if __name__ == "__main__":
    print("=" * 60)
    print("League Baselines & Percentile Analysis")
    print("=" * 60)
    
    baselines = LeagueBaselines()
    
    # Calculate 2025 league percentiles
    print("\n📊 Calculating 2025 League Percentiles...")
    percentiles = baselines.calculate_league_percentiles(season=2025, min_pa=100)
    
    if percentiles:
        print("\n📈 Key Metric Percentiles:")
        print("\nwRC+ (League Average = 100):")
        for p in [10, 25, 50, 75, 90]:
            val = percentiles['wrc_plus'][f'p{p}']
            print(f"   {p}th percentile: {val:.0f}")
        
        print("\nBABIP:")
        for p in [10, 25, 50, 75, 90]:
            val = percentiles['babip'][f'p{p}']
            print(f"   {p}th percentile: {val:.3f}")
        
        print("\nK%:")
        for p in [10, 25, 50, 75, 90]:
            val = percentiles['k_pct'][f'p{p}']
            print(f"   {p}th percentile: {val:.1f}%")
    
    # Test with Harrison Bader
    print("\n\n🔍 Testing with Harrison Bader 2024...")
    
    session = get_session()
    result = session.execute(
        text("""
            SELECT 
                p.name,
                ss.wrc_plus, ss.babip, ss.bb_pct, ss.k_pct, 
                ss.iso, ss.avg, ss.obp, ss.slg
            FROM season_stats ss
            JOIN players p ON ss.player_id = p.player_id
            WHERE p.name = 'Harrison Bader' AND ss.season = 2024
        """)
    ).fetchone()
    session.close()
    
    if result:
        player_stats = {
            'wrc_plus': result[1],
            'babip': result[2],
            'bb_pct': result[3],
            'k_pct': result[4],
            'iso': result[5],
            'avg': result[6],
            'obp': result[7],
            'slg': result[8]
        }
        
        comparison = baselines.compare_player_to_league(player_stats, season=2024, min_pa=100)
        
        print(f"\n📊 {result[0]} vs 2024 League:")
        for metric, data in sorted(comparison.items(), key=lambda x: x[1]['percentile'], reverse=True):
            val = data['value']
            pct = data['percentile']
            tier = data['tier']
            
            # Format value based on metric
            if metric in ['AVG', 'OBP', 'SLG', 'BABIP', 'ISO']:
                val_str = f"{val:.3f}"
            elif metric in ['BB%', 'K%']:
                val_str = f"{val:.1f}%"
            else:
                val_str = f"{val:.0f}"
            
            print(f"   {metric:8s}: {val_str:>7s} - {pct:3d}th percentile ({tier})")
    
    # Calculate role cohort stats
    print("\n\n📊 Calculating Role Cohort Statistics (2025)...")
    cohort_stats = baselines.calculate_role_cohort_stats(season=2025, min_pa=100)
    
    if cohort_stats:
        print("\n📈 Average Stats by Role:")
        for role, stats in cohort_stats.items():
            if stats['player_count'] >= 3:  # Only show roles with 3+ players
                print(f"\n   {role} ({stats['player_count']} players):")
                print(f"      wRC+: {stats['avg_wrc_plus']:.0f}")
                print(f"      BABIP: {stats['avg_babip']:.3f}")
                print(f"      K%: {stats['avg_k_pct']:.1f}%")
                print(f"      BB%: {stats['avg_bb_pct']:.1f}%")
                print(f"      ISO: {stats['avg_iso']:.3f}")