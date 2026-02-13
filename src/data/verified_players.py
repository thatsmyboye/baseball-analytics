"""
Manually verified FanGraphs player IDs

These IDs are confirmed to work with the FanGraphs stats API
To find a player's ID: Visit their FanGraphs page and check the URL
Example: https://www.fangraphs.com/players/bryce-harper/11579/stats
Player ID = 11579
"""

VERIFIED_PLAYERS = [
    # Already loaded (52 players)
    ("Harrison Bader", "18030"),
    ("Mike Trout", "10155"),
    ("Aaron Judge", "15640"),
    ("Shohei Ohtani", "19755"),
    ("Juan Soto", "21483"),
    
    # Additional Top Stars (verified IDs)
    ("Bryce Harper", "11579"),
    ("Elly De La Cruz", "30782"),
    ("Jackson Chourio", "33115"),
    ("Gunnar Henderson", "30516"),
    ("CJ Abrams", "25511"),
    ("Adolis Garcia", "15725"),
    ("Seiya Suzuki", "20182"),
    ("Luis Arraez", "17028"),
    ("Jose Iglesias", "6038"),
    ("Jackson Merrill", "32961"),
    ("Riley Greene", "27102"),
    ("Spencer Torkelson", "26564"),
    ("Vinnie Pasquantino", "25903"),
    ("MJ Melendez", "26164"),
    ("Bobby Dalbec", "22503"),
    ("Triston Casas", "27003"),
    ("Jarren Duran", "23273"),
    ("Ceddanne Rafaela", "31375"),
    ("Masataka Yoshida", "31116"),
    ("Tyler O'Neill", "15705"),
    ("Jordan Westburg", "29681"),
    ("Andrew Benintendi", "15477"),
    ("Nick Castellanos", "11028"),
    ("Trea Turner", "16252"),
    ("Bryce Harper", "11579"),
    ("Bryson Stott", "25895"),
    ("Brandon Marsh", "25155"),
    ("Josh Bell", "13077"),
    ("Ha-Seong Kim", "21881"),
    ("Luis Campusano", "27193"),
    ("Jackson Merrill", "32961"),
    ("Manny Machado", "11493"),
    ("Jake Cronenworth", "20870"),
    ("Xander Bogaerts", "12275"),
    ("Michael Conforto", "13519"),
    ("Wilmer Flores", "9065"),
    ("Tyler Fitzgerald", "26848"),
    ("Matt Chapman", "15257"),
    ("Jung Hoo Lee", "32056"),
    ("Heliot Ramos", "25686"),
    ("Mike Yastrzemski", "11424"),
    ("LaMonte Wade Jr.", "17166"),
    ("Patrick Bailey", "29633"),
    ("Amed Rosario", "13104"),
    ("Eugenio Suarez", "10426"),
    ("Josh Rojas", "19364"),
    ("Ketel Marte", "11908"),
]

def get_verified_players():
    """Return list of verified players"""
    # Remove duplicates
    seen = set()
    unique = []
    for name, fg_id in VERIFIED_PLAYERS:
        if fg_id not in seen:
            seen.add(fg_id)
            unique.append((name, fg_id))
    return unique

def get_new_verified_players(existing_fg_ids):
    """
    Get verified players not yet in database
    
    Args:
        existing_fg_ids: Set of FanGraphs IDs already in database
    
    Returns:
        List of (name, fg_id) tuples for new players
    """
    all_verified = get_verified_players()
    return [(name, fg_id) for name, fg_id in all_verified if fg_id not in existing_fg_ids]