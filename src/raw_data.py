import pandas as pd
import math

from apis import init_lichess_api, init_gspread_api
from awards import compute_compensation
from gspread_utils import download_as_dataframe, upload_dataframe


def update_raw_data(client, spreadsheet):
    df, header = download_as_dataframe(spreadsheet, 'RawData', 'RawData')

    df = df.set_index(['ID'])
    df['Round'] = pd.to_numeric(df['Round'])

    for game in client.games.export_multi(*df[df['Round'] > 85].index, evals=True, opening=True):
        game_id = game['id']


        start_date = game['createdAt'].timestamp()
        df.loc[game_id, 'Start_Date'] = int(round(start_date))

        moves = game['moves'].split(' ')

        players = game['players']
        df.loc[game_id, 'White'] = players['white']['user']['id']
        df.loc[game_id, 'Black'] = players['black']['user']['id']

        if len(moves) >= 4:
            df.loc[game_id, 'W_Move_1'] = moves[0]
            df.loc[game_id, 'B_Move_1'] = moves[1]

            df.loc[game_id, 'w_total_moves'] = math.ceil(len(moves)/2)
            df.loc[game_id, 'b_total_moves'] = math.floor(len(moves)/2)

        status = game['status']

        if status != 'started':
            if 'analysis' in players['white']:
                df.loc[game_id, 'White_Accuracy'] = int(players['white']['analysis']['acpl'])
                df.loc[game_id, 'Black_Accuracy'] = int(players['black']['analysis']['acpl'])

                w_comp, b_comp = compute_compensation(game)

                df.loc[game_id, 'w_comp'] = w_comp
                df.loc[game_id, 'b_comp'] = b_comp

                df.loc[game_id, 'w_total_CPL'] = int(players['white']['analysis']['acpl']) * math.ceil(len(moves)/2)
                df.loc[game_id, 'b_total_CPL'] = int(players['black']['analysis']['acpl']) * math.floor(len(moves)/2)

            # Update the game results.
            if status in {'resign', 'cheat', 'outoftime', 'mate'}:
                df.loc[game_id, 'Results'] = '0 - 1' if game['winner'] == 'black' else '1 - 0'
            else:
                df.loc[game_id, 'Results'] = '1/2 - 1/2'

            # Update the termination types.
            term_map = {'outoftime': 'Clock Flag', 'resign': 'Resign', 'mate': 'Mate', 'draw': 'Draw by Agreement', 'cheat': 'Banned'}
            df.loc[game_id, 'Termination'] = term_map[status]

            # Update when the game terminated and how long it lasted.
            termination_date = game['lastMoveAt'].timestamp()
            df.loc[game_id, 'Termination_Date'] = int(round(termination_date))
            df.loc[game_id, 'Duration'] = int(round(termination_date) - round(start_date))

            df.loc[game_id, 'Opening'] = game['opening']['eco']

    df = df.reset_index()
    
    print(df)
    upload_dataframe(spreadsheet, 'RawData', 'RawData', df, header)


if __name__ == '__main__':
    sh = init_gspread_api()
    client = init_lichess_api()

    update_raw_data(client, sh)