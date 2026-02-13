"""
Player Role Classification System

Classifies players into roles based on:
- Playing time patterns (PA per team game)
- Platoon splits (vs L/R)
- Leverage situations (gmLI)
- Defensive usage patterns
"""
import pandas as pd
from sqlalchemy import text
from src.utils.db_connection import get_session

class RoleClassifier:
    """
    Classify players into usage-based roles
    """
    
    ROLE_DEFINITIONS = {
        'EVERYDAY_REGULAR': 'Regular starter playing full time',
        'EVERYDAY_PLATOON_LEANING': 'Everyday player with platoon tendencies',
        'STRONG_SIDE_PLATOON': 'Platoon player getting most PAs vs one handedness',
        'HIGH_LEVERAGE_ROLE_PLAYER': 'Regular playing time in high-leverage situations',
        'ROTATIONAL_REGULAR': 'Regular rotation, not quite everyday',
        'DEFENSIVE_REPLACEMENT': 'Primarily used for defensive purposes',
        'BENCH_BAT': 'Primarily pinch-hitting role',
        'UTILITY_DEPTH': 'Sporadic playing time, multiple positions',
        'FRINGE_ROSTER': 'Minimal playing time',
    }
    
    def classify_season(self, player_id, season, games_played, pa, team_games=162):
        """
        Classify a player's role for a specific season
        
        Args:
            player_id: Database player_id
            season: Season year
            games_played: Player's games played
            pa: Player's plate appearances
            team_games: Team's total games (default 162)
        
        Returns:
            dict with role, confidence, and metrics
        """
        
        # Calculate key metrics
        pa_per_team_game = pa / team_games if team_games > 0 else 0
        games_played_pct = games_played / team_games if team_games > 0 else 0
        avg_pa_per_game = pa / games_played if games_played > 0 else 0
        
        # Decision tree based on usage
        # Everyday Regular: High PA/game rate and plays most games
        if pa_per_team_game >= 3.5 and games_played_pct >= 0.75:
            role = 'EVERYDAY_REGULAR'
            confidence = 0.95
        
        # Everyday but less consistent
        elif pa_per_team_game >= 3.0 and games_played_pct >= 0.65:
            role = 'EVERYDAY_REGULAR'
            confidence = 0.90
        
        # Rotational Regular: Plays regularly but not every day
        elif pa_per_team_game >= 2.0:
            role = 'ROTATIONAL_REGULAR'
            confidence = 0.85
        
        # Utility/Depth: Regular playing time but sporadic
        elif pa_per_team_game >= 1.0:
            if games_played_pct < 0.25:
                role = 'DEFENSIVE_REPLACEMENT'
                confidence = 0.75
            else:
                role = 'UTILITY_DEPTH'
                confidence = 0.75
        
        # Fringe roster
        else:
            role = 'FRINGE_ROSTER'
            confidence = 0.90
        
        return {
            'role': role,
            'confidence': confidence,
            'pa_per_team_game': pa_per_team_game,
            'games_played_pct': games_played_pct,
            'avg_pa_per_game': avg_pa_per_game,
        }
    
    def classify_all_seasons(self, player_id=None):
        """
        Classify roles for all player-seasons in database
        
        Args:
            player_id: Optional - classify only this player
        
        Returns:
            DataFrame with classifications
        """
        session = get_session()
        
        try:
            # Query season stats
            query = """
                SELECT 
                    ss.player_id,
                    p.name,
                    ss.season,
                    ss.team,
                    ss.games,
                    ss.pa
                FROM season_stats ss
                JOIN players p ON ss.player_id = p.player_id
                WHERE ss.games IS NOT NULL AND ss.pa IS NOT NULL
            """
            
            if player_id:
                query += f" AND ss.player_id = {player_id}"
            
            query += " ORDER BY ss.season, p.name"
            
            df = pd.read_sql(query, session.bind)
            
            if df.empty:
                print("No data found")
                return pd.DataFrame()
            
            # Classify each season
            classifications = []
            
            for _, row in df.iterrows():
                # Estimate team games (handle shortened seasons)
                if row['season'] == 2020:
                    team_games = 60  # COVID season
                else:
                    team_games = 162
                
                result = self.classify_season(
                    row['player_id'],
                    row['season'],
                    row['games'],
                    row['pa'],
                    team_games
                )
                
                classifications.append({
                    'player_id': row['player_id'],
                    'name': row['name'],
                    'season': row['season'],
                    'team': row['team'],
                    'games': row['games'],
                    'pa': row['pa'],
                    'role': result['role'],
                    'confidence': result['confidence'],
                    'pa_per_team_game': result['pa_per_team_game'],
                    'games_played_pct': result['games_played_pct'],
                })
            
            return pd.DataFrame(classifications)
        
        finally:
            session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Player Role Classification System")
    print("=" * 60)
    
    classifier = RoleClassifier()
    
    # Test with Harrison Bader
    print("\n🔍 Testing with Harrison Bader...")
    
    # Get Harrison Bader's player_id
    session = get_session()
    result = session.execute(
        text("SELECT player_id FROM players WHERE name = 'Harrison Bader'")
    ).fetchone()
    session.close()
    
    if result:
        bader_id = result[0]
        
        # Classify all his seasons
        classifications = classifier.classify_all_seasons(player_id=bader_id)
        
        print(f"\n📊 Harrison Bader Role History:")
        print(classifications[['season', 'team', 'games', 'pa', 'role', 'confidence']].to_string(index=False))
        
        print(f"\n📈 Role Distribution:")
        role_counts = classifications['role'].value_counts()
        for role, count in role_counts.items():
            print(f"   {role}: {count} seasons")
    
    # Now classify ALL players
    print("\n\n🔄 Classifying all players in database...")
    all_classifications = classifier.classify_all_seasons()
    
    print(f"\n✅ Classified {len(all_classifications)} player-seasons")
    print(f"\n📊 Overall Role Distribution:")
    role_counts = all_classifications['role'].value_counts()
    for role, count in role_counts.items():
        pct = count / len(all_classifications) * 100
        print(f"   {role}: {count} ({pct:.1f}%)")
    
    # Show some examples
    print(f"\n📋 Sample Classifications:")
    sample = all_classifications.sample(min(10, len(all_classifications)))
    print(sample[['name', 'season', 'games', 'pa', 'role']].to_string(index=False))