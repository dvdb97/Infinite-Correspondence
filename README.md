# Infinite-Correspondence

## Getting started

You will need:

- To generate a [Lichess API token](https://lichess.org/account/oauth/token) and place it into "auth/lichess.txt".
- To follow the instructions [here](https://docs.gspread.org/en/latest/oauth2.html#service-account) to create a service account key

Then run:

- `pip install gspread berserk chess pandas networkx matplotlib`

## Workflow

In general, most of the sheets have a Backend sheet to go along with it. Any edits to the sheet should be made in these.

## The scripts

Whilst these are mostly self-explanatory, there are a few that require some manual work at times. Those are explained in more detail below.

### raw_data.py

This is the main script that keeps track of the games. What we still need to do manually is:

- Enter the game Id in the ID column
- Enter the round number
- Enter the players in the corresponding color column
- Write 'game' in the Results column

Then you can run the script. Previously there was a bug where the columns 'White_Accuracy', 'Black_Accuracy', 'Start_Date', 'Termination_Date', 'Duration', 'w_comp', and 'b_comp' were not being formatted as Integer columns. This would sometimes break other parts of the spreadsheet. If this occurs, you can fix this manually by selecting those columns and then going 'Format' -> 'Number' -> 'Custom number format'.

### pairings.py

This script is run each week to generate the pairings. To have the most up to date pairings, run players.py and raw_data.py first. If there is an odd number of players, find someone to pair twice, pair them against another player, set that player temporarily to inactive and run the pairing script again.

### players.py

This script ensures the Players_Backend and Players sheets are in sync.

### awards.py

This script is mostly still work in progress.
