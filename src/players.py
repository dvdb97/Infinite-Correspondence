import pandas as pd

from berserk import Client

from apis import init_lichess_api, init_gspread_api
from gspread_utils import download_as_dataframe, upload_dataframe


def update_player_data(client: Client, spreadsheet):
    df, header = download_as_dataframe(spreadsheet, 'Players_Backend', 'PlayersRaw')

    df = df.set_index(['id'])

    print(df)

    for id in df.index:
        player = client.users.get_by_id(id)[0]

        df.loc[id, 'name'] = player['username']
        df.loc[id, 'corr_rtg'] = player['perfs']['correspondence']['rating']
        df.loc[id, 'class_rtg'] = player['perfs']['classical']['rating']

    df = df.reset_index()

    upload_dataframe(sh, 'Players_Backend', 'PlayersRaw', df, header)


if __name__ == '__main__':
    sh = init_gspread_api()
    client = init_lichess_api()
    
    update_player_data(client, sh)