import json
import os
import pandas as pd
from datetime import datetime
from pprint import pprint

class DataAPI():
    # Set directories for caching and data storage
    def __init__(self):
        self.cache_dir = 'api_cache'
        self.game_data_dir = '../data/stats/games'
        self.player_data_dir = '../data/stats/player'
        self.odds_data_dir = '../data/odds/prop'
        self.meta_dir = '../data/meta'
        self.game_data = None
        
        # Load player index mapping
        with open(f'{self.meta_dir}/player_idx.json', 'r') as f:
            self.player_idx = json.load(f)
        # Reverse the mapping to have ID -> player name
        self.player_idx = {v: k for k, v in self.player_idx.items()}
        
    def load_game_data(self):
        game_data = {}
        # Iterating over all files in the game data directory
        for file in os.listdir(self.game_data_dir):
            if not file.endswith('.json'):
                continue
            with open(f'{self.game_data_dir}/{file}', 'r') as f:
                data = json.load(f)
            # Parsing the date and group games by date
            date = datetime.strptime(data['date'], '%Y%m%d').strftime('%Y-%m-%d')
            if date not in game_data:
                game_data[date] = []
            game_data[date].append(data)
        return game_data
            
    def load_player_data(self):
        # Load game data
        self.game_data = self.load_game_data()
        self.dates = sorted(list(self.game_data.keys()))
        df_skeleton = {}
        for date in self.dates:
            games = self.game_data[date]
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            for game in games:
                box_score = game['box_score']
                player_idx = list(box_score.keys())
                home_players, away_players = [], []
                for idx in player_idx:
                    if box_score[idx]['home']:
                        home_players.append(self.player_idx[idx])
                    else:
                        away_players.append(self.player_idx[idx])

                for idx in player_idx:
                    player = self.player_idx[idx]
                    if player not in df_skeleton:
                        df_skeleton[player] = []
                    stats = box_score[idx].copy()
                    stats['opponent'] = ','.join(away_players) if stats['home'] else ','.join(home_players)
                    stats['team'] = home_players if stats['home'] else away_players
                    stats['team'] = ','.join([p for p in stats['team'] if p != player])
                    stats['date'] = date_obj
                    df_skeleton[player].append(stats)

        # Converting each player's data to a DataFrame and saving
        for player in df_skeleton:
            df = pd.DataFrame(df_skeleton[player])
            df = df.set_index('date')
            df.to_csv(f'{self.player_data_dir}/{player}.csv')
        return
    
    def load_player_stats(self, player):
        df = pd.read_csv(f'{self.player_data_dir}/{player}.csv')
        df = df.set_index('date')
        return df

    def fix_odds_dates(self, player, player_df):
        stats_df = self.load_player_stats(player)
        stats_df = stats_df.reset_index()
        stats_df['date'] = pd.to_datetime(stats_df['date'])
        dates = stats_df['date'].unique()

        # match the dates in player_df to the closest date in stats_df
        player_df = player_df.reset_index()
        player_df['date'] = pd.to_datetime(player_df['date'])

        for i, row in player_df.iterrows():
            date = row['date']
            if date in dates:
                continue
            closest_date = min(dates, key=lambda x: abs(x - date))
            player_df.loc[i, 'date'] = closest_date

        player_df = player_df.set_index('date')
        player_df.sort_index(inplace=True)
        return player_df
    
    def load_player_odds_data(self):
        dfs = []
        for file in os.listdir(self.odds_data_dir + '/date'):
            if not file.endswith('.csv'):
                continue
            df = pd.read_csv(f'{self.odds_data_dir}/date/{file}')
            df = df.set_index('date')
            dfs.append(df)
        
        df = pd.concat(dfs)
        players = df['player'].unique()
        for player in players:
            df_player = df[df['player'] == player]
            df_player = self.fix_odds_dates(player, df_player)
            df_player.to_csv(f'{self.odds_data_dir}/player/{player}.csv')

    def get_player_data(self, player):
        df = pd.read_csv(f'{self.player_data_dir}/{player}.csv')
        df = df.set_index('date')
        return df
    
    def get_player_odds_data(self, player):
        df = pd.read_csv(f'{self.odds_data_dir}/player/{player}.csv')
        df = df.set_index('date')
        return df
    
if __name__ == '__main__':
    api = DataAPI()
    api.load_player_data()
    # api.load_player_odds_data()