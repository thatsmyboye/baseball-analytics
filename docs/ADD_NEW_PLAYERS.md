# Adding New Players to the Database

## ⭐ RECOMMENDED: Use Pybaseball (NEW!)

The easiest way to add players is now using pybaseball integration:
```bash
python src/scripts/add_players_interactive.py
```

This will:
1. ✅ Automatically find FanGraphs IDs (no manual lookup!)
2. ✅ Verify IDs work before loading
3. ✅ Load all stats (2015-2025) automatically
4. ✅ Handle errors gracefully

### Quick Example
```
$ python src/scripts/add_players_interactive.py

First name: Bryce
Last name: Harper
  ✓ Added to queue: Bryce Harper

First name: Mookie  
Last name: Betts
  ✓ Added to queue: Mookie Betts

First name: done

🔍 Looking up 2 players...
   Bryce Harper... ✅ FG ID: 11579
   Mookie Betts... ✅ FG ID: 13611

✅ Found 2 players with FanGraphs IDs

Load these 2 players? (yes/no): yes

[1/2] Bryce Harper...
   Scraping 2015-2025...
   ✅ Success! Loaded 10 seasons
```

---