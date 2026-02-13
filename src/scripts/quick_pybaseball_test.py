"""
Quick test of pybaseball integration
"""
from pybaseball import playerid_lookup, batting_stats, cache

cache.enable()

print("=" * 70)
print("PYBASEBALL QUICK TEST")
print("=" * 70)

# Test 1: Player ID Lookup
print("\n1️⃣ Testing Player ID Lookup...")
player = playerid_lookup('judge', 'aaron')
print(f"\nAaron Judge:")
print(f"  FanGraphs ID: {player['key_fangraphs'].iloc[0]}")
print(f"  MLBAM ID: {player['key_mlbam'].iloc[0]}")
print(f"  Baseball Ref: {player['key_bbref'].iloc[0]}")

# Test 2: Get Season Stats
print("\n\n2️⃣ Testing Season Stats Retrieval...")
stats_2024 = batting_stats(2024, qual=200)
print(f"\nRetrieved {len(stats_2024)} qualified batters from 2024")
print(f"\nSample columns: {list(stats_2024.columns[:10])}")

# Test 3: Find a specific player's stats
print("\n\n3️⃣ Finding Aaron Judge 2024 stats...")
judge_stats = stats_2024[stats_2024['Name'] == 'Aaron Judge']

if not judge_stats.empty:
    print(f"\nAaron Judge 2024:")
    print(f"  PA: {judge_stats['PA'].iloc[0]:.0f}")
    print(f"  HR: {judge_stats['HR'].iloc[0]:.0f}")
    print(f"  wRC+: {judge_stats['wRC+'].iloc[0]:.0f}")
    print(f"  BABIP: {judge_stats['BABIP'].iloc[0]:.3f}")

print("\n✅ Pybaseball is working!")
print("\nRecommendation: Integrate for player ID lookup immediately.")