# NBA-NFL-predictor

`api.py`: The DataAPI class manages statistics and betting odds data for individual players. I initialize directory paths for different types of data, including game stats, player stats, and betting odds. The class can load and group game data by date, extract and structure player statistics, align odds data with the closest available game dates, and save this data. By reversing the player index dictionary, I efficiently map between player IDs and names easily retrieve game and odds data for individual players.

`predictions.ipynb`: I use historical player performance data and logistic regression and random forest classifiers. I use the DataAPI class to train logistic regression and random forest models using time-series cross-validation and calculate betting probabilities. I then summarize the the output into `bet_df.csv`. 

`pts_model.ipynb`: We can input a specific player, (in this case Mikal Bridges), and a specific market (in this case "player points over/under"). It assesses betting accuracy and calculates cumulative returns. This provides insights into the profitability of betting strategies using historical player data.