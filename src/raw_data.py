import pandas as pd

from apis import init_lichess_api, init_gspread_api
from gspread_utils import download_as_dataframe, upload_dataframe


def update_raw_data(client, spreadsheet):
    df, header = download_as_dataframe(spreadsheet, 'RawData', 'RawData')
    df = df.set_index(['ID'])
    df['Round'] = pd.to_numeric(df['Round'])

    for game in client.games.export_multi(*df.index, evals=True, opening=True):
        start_date = game['createdAt'].strftime('%Y-%m-%d')
        df.loc[game['id'], 'Start_Date'] = start_date

        moves = game['moves'].split(' ')

        if len(moves) >= 4:
            df.loc[game['id'], 'W_Move_1'] = moves[0]
            df.loc[game['id'], 'B_Move_1'] = moves[1]

        if game['status'] != 'started':
            players = game['players']

            if 'analysis' in players['white']:
                df.loc[game['id'], 'White_Accuracy'] = players['white']['analysis']['acpl']
                df.loc[game['id'], 'Black_Accuracy'] = players['black']['analysis']['acpl']

            termination_date = game['lastMoveAt'].strftime('%Y-%m-%d')
            df.loc[game['id'], 'Termination_Date'] = termination_date
            df.loc[game['id'], 'Opening'] = game['opening']['eco']

    df = df.reset_index()

    upload_dataframe(spreadsheet, 'RawData', 'RawData', df, header)


if __name__ == '__main__':
    sh = init_gspread_api()
    client = init_lichess_api()

    update_raw_data(client, sh)