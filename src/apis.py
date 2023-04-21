import berserk
import gspread

from berserk import Client, TokenSession
from gspread import Spreadsheet


def init_lichess_api() -> Client:
    with open('auth/lichess.txt') as f:
        lichess_auth_token = f.read()
        
        session = TokenSession(lichess_auth_token)
        client = Client(session=session)

        return client
    

def init_gspread_api() -> Spreadsheet:
    gc = gspread.service_account()
    sh = gc.open("Lichess4545 - Infinite Correspondence")

    return sh