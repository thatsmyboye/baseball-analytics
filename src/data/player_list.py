"""
Top MLB players by position - Mix of stars and regulars
FanGraphs IDs collected from their player pages
"""

TOP_PLAYERS = [
    # Catchers
    ("J.T. Realmuto", "11739"),
    ("Will Smith", "19144"),
    ("Salvador Perez", "5782"),
    ("Adley Rutschman", "25475"),
    ("Cal Raleigh", "23778"),
    
    # First Base
    ("Freddie Freeman", "5361"),
    ("Matt Olson", "17158"),
    ("Vladimir Guerrero Jr.", "19611"),
    ("Pete Alonso", "19251"),
    ("Paul Goldschmidt", "8973"),
    
    # Second Base
    ("Marcus Semien", "12561"),
    ("Jose Altuve", "5417"),
    ("Gleyber Torres", "17976"),
    ("Ozzie Albies", "17054"),
    ("Ketel Marte", "11908"),
    
    # Shortstop
    ("Bobby Witt Jr.", "24119"),
    ("Corey Seager", "11479"),
    ("Trea Turner", "13510"),
    ("Francisco Lindor", "12916"),
    ("Dansby Swanson", "16530"),
    
    # Third Base
    ("Jose Ramirez", "11493"),
    ("Rafael Devers", "17350"),
    ("Austin Riley", "18886"),
    ("Manny Machado", "11493"),
    ("Nolan Arenado", "9777"),
    
    # Outfield
    ("Mike Trout", "10155"),
    ("Aaron Judge", "15640"),
    ("Shohei Ohtani", "19755"),
    ("Juan Soto", "21483"),
    ("Mookie Betts", "13611"),
    ("Ronald Acuna Jr.", "18401"),
    ("Kyle Tucker", "18930"),
    ("Randy Arozarena", "19384"),
    ("Yordan Alvarez", "21318"),
    ("Fernando Tatis Jr.", "21529"),
    ("Julio Rodriguez", "25527"),
    ("Corbin Carroll", "26138"),
    ("Jazz Chisholm Jr.", "22408"),
    ("Kyle Schwarber", "14113"),
    ("Christian Yelich", "11477"),
    ("George Springer", "11404"),
    ("Teoscar Hernandez", "15399"),
    ("Harrison Bader", "18030"),
    ("Bryan Reynolds", "19863"),
    ("Anthony Santander", "15711"),
    
    # More OF
    ("Ian Happ", "15757"),
    ("Cedric Mullins", "19363"),
    ("Steven Kwan", "25415"),
    ("Jesse Winker", "14916"),
    ("Michael Harris II", "25934"),
    ("Jarren Duran", "23273"),
    ("Riley Greene", "25696"),
    
    # Additional IF
    ("Gunnar Henderson", "26165"),
    ("Wander Franco", "24141"),
    ("Nico Hoerner", "21755"),
    ("Jorge Polanco", "12973"),
    ("Jonathan India", "23649"),
    
    # DH / Utility
    ("Giancarlo Stanton", "4949"),
    ("Yordan Alvarez", "21318"),
    ("J.D. Martinez", "7173"),
]

# Remove duplicates
TOP_PLAYERS = list(dict.fromkeys(TOP_PLAYERS))

def get_all_players():
    """Return the full player list"""
    return TOP_PLAYERS

def get_players_by_count(n=50):
    """Return first n players"""
    return TOP_PLAYERS[:n]