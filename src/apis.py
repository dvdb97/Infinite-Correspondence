import gspread

from berserk import Client, TokenSession
from gspread import Spreadsheet


class TimeoutTokenSession(TokenSession):
    """TokenSession that enforces a default timeout on every request.

    requests.Session has no timeout by default, so a stalled connection
    (e.g. Lichess hiccup while streaming export_multi) can hang forever.
    """

    def __init__(self, token: str, timeout: float = 30):
        super().__init__(token)
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return super().request(method, url, **kwargs)


def init_lichess_api() -> Client:
    with open('auth/lichess.txt') as f:
        lichess_auth_token = f.read()
        
        session = TimeoutTokenSession(lichess_auth_token)
        client = Client(session=session)

        return client
    

def init_gspread_api() -> Spreadsheet:
    gc = gspread.service_account()
    gc.set_timeout(30)  # gspread has no default timeout; avoid indefinite hangs on stalled requests.
    sh = gc.open("Lichess4545 - Infinite Correspondence")

    return sh