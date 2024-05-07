import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
import json
from pprint import pprint
import os
import pandas as pd

with open('NBA/meta/player_idx.json', 'r') as f:
    nba_player_idx = json.load(f)

with open('NFL/meta/player_idx.json', 'r') as f:
    nfl_player_idx = json.load(f)

def find_name(string):
    for name in nba_player_idx:
        if name in string:
            return name
    for name in nfl_player_idx:
        if name in string:
            return name
    return None

class OddsAPI():

    def __init__(self, api_key):

        self.base = 'https://api.prop-odds.com/beta'
        self.markets = {
            'NBA': [
                'player_assists_over_under', 
                'player_blocks_over_under', 
                'player_points_over_under', 
                'player_rebounds_over_under', 
                'player_steals_over_under', 
                'player_threes_over_under'
            ],
            'NFL': [
                'player_td_over_under',
                'player_tackles_over_under',
                'player_tackles_and_assists_over_under',
                'player_sacks_over_under',
                'player_rushing_yds_over_under',
                'player_rushing_attempts_over_under',
                'player_rushing_and_receiving_yards_over_under',
                'player_receptions_over_under',
                'player_receptions_over_under',
                'player_receiving_yds_over_under',
                'player_passing_yds_over_under',
                'player_passing_tds_over_under',
                'player_passing_completions_over_under',
                'player_passing_attempts_over_under',
                'player_passing_and_rushing_yds_over_under',
            ]
        }
            
        self.api_key = api_key
        self.meta_dir = 'meta'
        self.prop_data_dir = 'odds/prop/date'
        self.init()

    def init(self):
        data = requests.get(self.base + '/usage' + f'?api_key={self.api_key}').json()
        print(f'Usage: {data["used"]} / {data["limit"]}')

    def get_game_ids(self, start_date, end_date, league='NBA', _log=True):
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        with open(f'{league}/{self.meta_dir}/game_idx.json', 'r') as f:
            aggregate_data = json.load(f)
        for t in range((end - start).days):
            date = (start + timedelta(days=t)).strftime('%Y-%m-%d')
            if date in aggregate_data:
                continue
            if _log:
                print(f'Collecting GAME_ID [{date}]')
            data = requests.get(self.base + f'/games/{league}?date={date}&api_key={self.api_key}').json()
            # print(self.base + f'/games/{league}?date={date}&api_key={self.api_key}')
            games = data['games']
            # print(data)
            if not games:
                continue
            if date not in aggregate_data:
                aggregate_data[date] = {}
            for game in games:
                aggregate_data[date][game['game_id']] = {
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'start_time': game['start_timestamp'],
                }
        with open(f'{league}/{self.meta_dir}/game_idx.json', 'w') as f:
            json.dump(aggregate_data, f, indent=4)

    def get_prop_odds(self, start_date, end_date, league='NBA', _log=True):
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        with open(f'{league}/{self.meta_dir}/game_idx.json', 'r') as f:
            game_ids = json.load(f)

        for t in range((end - start).days):
            
            prop_data = []
            date = (start + timedelta(days=t)).strftime('%Y-%m-%d')
            if f'{date}.csv' in os.listdir(f'{league}/{self.prop_data_dir}') or date not in game_ids:
                continue

            if _log:
                print(f'Collecting PROPS [{date}]')
            for market in self.markets[league]:
                if _log:
                    print(f'  - Collecting {market} [{date}]')
                for game_id in game_ids[date]:
                    data = requests.get(self.base + f'/odds/{game_id}/{market}?api_key={self.api_key}').json()
                    # pprint(data)
                    if 'sportsbooks' not in data:
                        continue
                    for book in data['sportsbooks']:
                        book_key = book['bookie_key']
                        # pprint(book)
                        for odds in book['market']['outcomes']:
                            
                            name = find_name(odds['description'].lower()) or find_name(odds['name'].lower())
                            over = 'over' in odds['name'].lower() or 'over' in odds['description'].lower()
                            under = 'under' in odds['name'].lower() or 'under' in odds['description'].lower()

                            if not name:
                                continue
                            if odds['handicap'] < 0 or len(name) < 4:
                                continue
                            if not over and not under:
                                over = True

                            prop_data.append({
                                'date': date,
                                'game_id': game_id,
                                'book_key': book_key,
                                'market': market,
                                'player': name,
                                'over_under': over,
                                'value': odds['handicap'],
                                'odds': odds['odds'],   
                                'timestamp': odds['timestamp'],
                                'home_team': game_ids[date][game_id]['home_team'],
                                'away_team': game_ids[date][game_id]['away_team'],
                            })
            # pprint(prop_data)
            df = pd.DataFrame(prop_data)
            df.to_csv(f'{league}/{self.prop_data_dir}/{date}.csv', index=False)
            if _log:
                print(f'  - Saved {len(prop_data)} props [{date}]\n')


if __name__ == '__main__':
    api_key = 'qq37PYwT7xU6HEx7RoQ3FecyjKH7GTWUNmz6Or10XnM'
    api = OddsAPI(api_key)
    start = '2023-08-01'
    end = '2024-01-15'
    # api.get_game_ids('2023-08-01', '2024-01-01', league='NFL')
    # api.get_game_ids('2023-03-17', '2023-05-21')
    # api.get_game_ids('2023-10-23', '2023-10-31')
    api.get_prop_odds(start, end, league='NFL', _log=True)
