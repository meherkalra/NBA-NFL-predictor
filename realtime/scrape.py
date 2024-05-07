from bs4 import BeautifulSoup
from html.parser import HTMLParser
import json
import os


def make_float(num):
    try:
        return float(num)
    except ValueError:
        return -float(num[1:])

def scrape_lines(type='points', date='2023-11-10'):
    
    file_date = '_'.join(date.split('-'))
    with open(f'web_cache/{file_date}_{type}.html', 'r') as f:
        raw_html = f.read()

    soup = BeautifulSoup(raw_html, 'html.parser')
    
    lines = {}

    cards = soup.find_all('table', class_='sportsbook-table')
    for card in cards:
        rows = card.find_all('tr')
        
        for row in rows[1:]:
            player = row.find('th').a.span.text
            outcomes = row.find_all('div', class_='sportsbook-outcome-cell')
            line = make_float(outcomes[0].find('span', class_='sportsbook-outcome-cell__line').text)
            over_odds = make_float(outcomes[0].find('span', class_='sportsbook-odds american default-color').text)
            under_odds = make_float(outcomes[1].find('span', class_='sportsbook-odds american default-color').text)

            lines[player] = {
                'line': line,
                'over_odds': over_odds,
                'under_odds': under_odds
            }

    if date not in os.listdir('dates'):
        os.mkdir(f'dates/{date}')


    with open(f'dates/{date}/{type}.json', 'w') as f:
        json.dump(lines, f, indent=4)


if __name__ == '__main__':
    scrape_lines('steals', '2023-11-10')

# print(len(cards))
