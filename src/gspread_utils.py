import pandas as pd
import gspread as gs

from typing import List, Any, Tuple

from apis import init_gspread_api


def download_as_dataframe(spreadsheet, ws_name, table_name) -> Tuple[pd.DataFrame, List[Any]]:
    worksheet = spreadsheet.worksheet(ws_name)
    table = worksheet.get(table_name)
    df = pd.DataFrame(table[1:], columns=table[0])

    return df, table[0]


def upload_dataframe(spreadsheet: gs.Worksheet, ws_name, table_name, df: pd.DataFrame, header: List=None):
    worksheet = spreadsheet.worksheet(ws_name)
    table = df.values.tolist()

    print(header)

    if header is not None:
        table = [header] + table

    print(table)
    
    worksheet.update(table_name, table)
