import requests
from bs4 import BeautifulSoup
import json
from time import sleep
from tqdm import tqdm
import os
from random import uniform
from pprint import pprint
from unidecode import unidecode


with open('config.json', 'r') as f:
    config = json.load(f)

def build_player_idx_nba():
    player_idx = {}
    chars = 'abcdefghijklmnopqrstuvwxyz'
    for i in tqdm(range(26), desc='Building Player Index'):
        url = f'https://www.basketball-reference.com/players/{chars[i]}/#players'
        url = f''
        raw = requests.get(url)
        soup = BeautifulSoup(raw.text, 'html.parser')
        try:
            table = soup.find('table', {'id': 'players'})
        except:
            sleep(config['sleep'])
            i -= 1
            continue
        for row in table.find_all('tr'):
            strong = row.find('strong')
            if not strong: 
                continue
            name = strong.a.text
            idx = strong.a['href'].split('/')[-1][:-5]
            player_idx[unidecode(name.lower())] = idx
        sleep(config['sleep'])
    with open('meta/player_idx.json', 'w') as f:
        json.dump(player_idx, f, indent=4)


def build_player_idx_nfl():
    player_idx = {}
    chars = 'abcdefghijklmnopqrstuvwxyz'
    for i in tqdm(range(26), desc='Building Player Index'):
        url = f'https://www.pro-football-reference.com/players/{chars[i].upper()}/#players'
        raw = requests.get(url)
        soup = BeautifulSoup(raw.text, 'html.parser')
        try:
            table = soup.find('div', {'id': 'div_players'})
        except:
            sleep(config['sleep'])
            i -= 1
            continue
        for row in table.find_all('p'):
            name = row.a.text
            idx = row.a['href'].split('/')[-1][:-4]
            player_idx[unidecode(name.lower())] = idx
        sleep(config['sleep'])
    with open('NFL/meta/player_idx.json', 'w') as f:
        json.dump(player_idx, f, indent=4)

class BR_API(object):

    def __init__(self) -> None:
        self.base = 'https://www.basketball-reference.com'
        self.meta_dir = '../meta'
        self.cache_dir = '../cache'
        with open(f'{self.meta_dir}/player_idx.json', 'r') as f:
            self.player_idx = json.load(f)
        with open(f'{self.meta_dir}/teams.json', 'r') as f:
            self.teams = json.load(f)

    def get_player_id(self, name):
        if name.lower() not in self.player_idx:
            return None
        return self.player_idx[name.lower()]
    
    def get_with_cache(self, ext):
        cache_page = ext.replace('/', '_')
        if cache_page in os.listdir(self.cache_dir):
            print(f'Using cache for {cache_page}')
            soup = BeautifulSoup(open(f'{self.cache_dir}/{cache_page}', 'r').read(), 'html.parser')
        else:
            print(f'Getting Data For ' + ext)
            raw = requests.get(self.base + '/' + ext)
            soup = BeautifulSoup(raw.text, 'html.parser')
            with open(f'{self.cache_dir}/{cache_page}', 'w') as f:
                f.write(soup.prettify())
            sleep(config['sleep'] + uniform(0, 2))
        return soup
    
    def get_team_rosters(self, year):
        rosters = {'players': {}, 'teams': {}}
        for team in self.teams:
            ext = f'teams/{team}/{year}.html'
            soup = self.get_with_cache(ext)
            table = soup.find('table', {'id': 'roster'})
            for row in table.find_all('tr')[1:]:
                name = row.find('td').text.strip()
                player_id = self.get_player_id(name)
                if not player_id: 
                    continue
                rosters['players'][player_id] = team
                rosters['teams'][team] = rosters['teams'].get(team, [])
                rosters['teams'][team].append(player_id)
        with open(f'{self.meta_dir}/rosters/rosters_{year}.json', 'w') as f:
            json.dump(rosters, f, indent=4)
    
    def get_box_score(self, date, game_id):
        ext = f'boxscores/{date}0{game_id}.html'
        soup = self.get_with_cache(ext)
        game_log = {}
        game_log['date'] = date
        visiting_team = soup.find_all('strong')[4].text.strip()
        home_team = soup.find_all('strong')[5].text.strip()
        game_log['visiting_team'] = visiting_team
        game_log['home_team'] = home_team

        game_log['home_team'] = home_team
        game_log['visiting_team'] = visiting_team
        
        scores = soup.find_all('div', {'class': 'score'})
        game_log['home_team_score'] = int(scores[1].text.strip())
        game_log['visiting_team_score'] = int(scores[0].text.strip())
        game_log['box_score'] = {}

        home_team_basic = soup.find('table', {'id': f'box-{home_team.upper()}-game-basic'})
        visiting_team_basic = soup.find('table', {'id': f'box-{visiting_team.upper()}-game-basic'})
        home_team_advanced = soup.find('table', {'id': f'box-{home_team.upper()}-game-advanced'})
        visiting_team_advanced = soup.find('table', {'id': f'box-{visiting_team.upper()}-game-advanced'})

        for n, table in enumerate([visiting_team_basic, home_team_basic, visiting_team_advanced, home_team_advanced]):
            for row in table.find_all('tr')[1:]:
                player = row.th.text.strip()
                if (player == 'Starters' or player == 'Reserves'): 
                    continue
                player_id = self.get_player_id(unidecode(player))
                if not player_id: 
                    continue

                for col in row.find_all('td'):
                    stat = col['data-stat']
                    if not stat or stat == 'reason': 
                        continue
                    game_log['box_score'][player_id] = game_log['box_score'].get(player_id, {})
                    if stat == 'mp':
                        minutes = int(col.text.strip().split(':')[0]) + int(col.text.strip().split(':')[1]) / 60
                        game_log['box_score'][player_id][stat] = round(minutes, 2)
                    else:
                        if col.text.strip():
                            game_log['box_score'][player_id][stat] = float(col.text.strip())
                        else:
                            game_log['box_score'][player_id][stat] = 0
                    game_log['box_score'][player_id]['home'] = int((n % 2 == 1))

        return game_log
            

    def get_game_logs(self, season='2023'):
        months = ['september', 'october', 'november', 'december', 
                  'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august']
        for m in months:
            ext = f'leagues/NBA_{season}_games-{m}.html'
            soup = self.get_with_cache(ext)
            table = soup.find('table', {'id': 'schedule'})
            if (not table): 
                continue
            for row in table.find_all('tr'):
                box_score = row.find('td', {'data-stat': 'box_score_text'})
                if not box_score or not box_score.a: 
                    continue
                box_score = box_score.a['href']
                date = box_score.split('/')[-1][:8]
                game_id = box_score.split('/')[-1][9:-5]
                if (f'{date}_{game_id}.json' in os.listdir('games')): 
                    continue
                box_score_parsed = self.get_box_score(date, game_id)                    
                with open(f'games/{date}_{game_id}.json', 'w') as f:
                    json.dump(box_score_parsed, f, indent=4)

if __name__ == "__main__":
    # br = BR_API()
    # build_player_idx()
    # br.get_game_logs('2024')
    build_player_idx_nfl()


    
                     
