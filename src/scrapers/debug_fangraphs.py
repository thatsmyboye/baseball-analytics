"""
Debug FanGraphs page structure
"""
import requests
from bs4 import BeautifulSoup

url = "https://www.fangraphs.com/leaders.aspx"

params = {
    'pos': 'all',
    'stats': 'bat',
    'lg': 'all',
    'qual': '50',
    'type': 'c',
    'season': '2025',
    'month': '0',
    'season1': '2025',
    'ind': '0',
    'team': '0',
    'rost': '0',
    'age': '0',
    'filter': '',
    'players': '0',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, params=params, headers=headers, timeout=30)

# Save raw HTML to file for inspection
with open('fangraphs_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("Saved raw HTML to fangraphs_page.html")

# Try to find tables
soup = BeautifulSoup(response.content, 'html.parser')

# Look for all tables
tables = soup.find_all('table')
print(f"\nFound {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"\nTable {i+1}:")
    print(f"  Classes: {table.get('class')}")
    print(f"  ID: {table.get('id')}")
    
# Look for player links
links = soup.find_all('a', href=lambda x: x and 'players' in str(x))
print(f"\nFound {len(links)} links with 'players' in href")

if links:
    print("\nFirst 5 player links:")
    for link in links[:5]:
        print(f"  {link.get('href')} - {link.text.strip()}")