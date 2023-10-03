import pandas as pd

from apis import init_lichess_api, init_gspread_api
from awards import compute_compensation
from gspread_utils import download_as_dataframe, upload_dataframe


def update_raw_data(client, spreadsheet):
    df, header = download_as_dataframe(spreadsheet, 'RawData', 'RawData')

    df = df.set_index(['ID'])
    df['Round'] = pd.to_numeric(df['Round'])

    for game in client.games.export_multi(*df[df['Round'] > 25].index, evals=True, opening=True):
        start_date = game['createdAt'].timestamp()
        df.loc[game['id'], 'Start_Date'] = round(start_date)

        moves = game['moves'].split(' ')

        players = game['players']
        df.loc[game['id'], 'White'] = players['white']['user']['id']
        df.loc[game['id'], 'Black'] = players['black']['user']['id']

        if len(moves) >= 4:
            df.loc[game['id'], 'W_Move_1'] = moves[0]
            df.loc[game['id'], 'B_Move_1'] = moves[1]

        if game['status'] != 'started':
            if 'analysis' in players['white']:
                df.loc[game['id'], 'White_Accuracy'] = players['white']['analysis']['acpl']
                df.loc[game['id'], 'Black_Accuracy'] = players['black']['analysis']['acpl']

                w_comp, b_comp = compute_compensation(game)

                df.loc[game['id'], 'w_comp'] = w_comp
                df.loc[game['id'], 'b_comp'] = b_comp

            df.loc[game['id'], ]

            termination_date = game['lastMoveAt'].timestamp()
            df.loc[game['id'], 'Termination_Date'] = round(termination_date)

            df.loc[game['id'], 'Opening'] = game['opening']['eco']

    df = df.reset_index()

    print(df)
    upload_dataframe(spreadsheet, 'RawData', 'RawData', df, header)


if __name__ == '__main__':
    sh = init_gspread_api()
    client = init_lichess_api()

    update_raw_data(client, sh)