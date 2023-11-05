from apis import init_lichess_api, init_gspread_api
from awards import compute_compensation
from gspread_utils import download_as_dataframe, upload_dataframe


scores = {
    0:      -800,
    0.5:    -366,
    1:      -240,
    1.5:    -149,
    2:	    -72,
    2.5:    0,
    3:      72,
    3.5:    149,
    4:      240,
    4.5:    366,
    5:      800
}


def compute_perf_rating(avg_opp_rtg: float, score: float) -> float:
    """Computes the performance rating for five games.

    Args:
        avg_opp_rtg (float): The average rating of the opponents
        score (float): The points scored against the opposition.
    Returns:
        float: Returns the performance rating.
    """
    return avg_opp_rtg + scores[score]


def compute_historical_rankings():
    sh = init_gspread_api()
    client = init_lichess_api()
    df, _ = download_as_dataframe(sh, 'RawData', 'RawData')
    df.sort_values("Termination_Date", axis=0, inplace=True)

    for row in df:
        

if __name__ == '__main__':
    compute_historical_rankings()