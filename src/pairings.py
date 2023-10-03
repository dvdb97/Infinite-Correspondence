import networkx as nx
import pandas as pd

from enum import Enum
from typing import List, Dict
from itertools import combinations
from functools import total_ordering

from apis import init_lichess_api, init_gspread_api
from gspread_utils import download_as_dataframe, upload_dataframe


@total_ordering
class ColorPref(Enum):
    WHITE = 1
    NEUTRAL = 2
    BLACK = 3

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        
        return NotImplemented


def get_k_recent_opponents(spreadsheet, players, k=5) -> Dict[str, List[str]]:
    """Extracts the recent k opponents for each players from the spreadsheet.

    Args:
        spreadsheet (_type_): The speadsheet to load the data from.
        players (_type_): The list of players to get the data for.
        k (int, optional): The number of recent games to consider. Defaults to 5. 

    Returns:
        Dict[str, List[str]]: Returns a dict containing the list of recent players for each
        player.
    """
    df, _ = download_as_dataframe(spreadsheet, 'RawData', 'RawData')
    print(df)
    df = df.set_index(['ID'])
    df['Round'] = pd.to_numeric(df['Round'])

    df_filtered = df[(df['White'].isin(players) | df['Black'].isin(players))]
    df_sorted = df_filtered.sort_values(by='Start_Date', ascending=False)

    recent_opps = dict()

    for player in players:
        df_recent = df_sorted[(df_sorted['White'] == player) | (df_sorted['Black'] == player)]
        recent_opps[player] = []

        for i in range(min(k, len(df_recent))):
            if df_recent['White'].iloc[i] == player:
                recent_opps[player] = recent_opps.get(player, []) + [df_recent['Black'].iloc[i]]
            else:
                recent_opps[player] = recent_opps.get(player, []) + [df_recent['White'].iloc[i]]

    return recent_opps


def generate_pairings(players: List[str], rtgs: Dict[str, float], recent_k_opps: Dict[str, List[str]], col_pref: Dict[str, ColorPref]):
    """Generates pairings for the given players based on their ratings, recent opponents and color
    preferences. It constraints the potential pairings to not include pairings that have recently
    occured.

    Args:
        players (List[str]): The players to pair.
        rtgs (Dict[str, float]): The player's ratings.
        recent_k_opps (Dict[str, List[str]]): The player's recent opponents.
        cols_pref (Dict[str, int]): The color preference for each player.
    """
    assert len(players) % 2 == 0, "Number of players can't be odd!"

    G = nx.Graph()
    G.add_nodes_from(players)

    # Connect two players with an edge iff they don't prefer the same color and haven't been matched recently.
    for a, b in combinations(players, 2):
        col_pref_check = not (col_pref[a] == col_pref[b] and col_pref[a] != ColorPref.NEUTRAL)

        if col_pref_check and b not in recent_k_opps[a]:
            G.add_edge(a, b, weight=abs(rtgs[a]-rtgs[b]))

    # Compute the pairings with a min weight matching on the created graph.
    pairings = nx.algorithms.matching.min_weight_matching(G)

    output = list()

    # pretty print the pairings.
    for a, b in pairings:
        if col_pref[a] <= col_pref[b]:
            output.append((a, b))
            print(f'@{ a } vs @{ b }')
        else:
            output.append((b, a))
            print(f'@{ b } vs @{ a }')

    return output


if __name__ == '__main__':
    spreadsheet = init_gspread_api()

    df, _ = download_as_dataframe(spreadsheet, 'Pairing_Maker', 'PairingMaker')
    df = df

    players = [player.lower() for player in df['Player']]
    pwr_rtgs = pd.to_numeric(df['Power Score']) 
    colors = map(
        lambda c: ColorPref.WHITE if c <= -1 else (ColorPref.BLACK if c >= 1 else ColorPref.NEUTRAL), 
        pd.to_numeric(df['Color Score'])
    )

    opps = get_k_recent_opponents(spreadsheet, players)
    print(opps)

    generate_pairings(
        players, 
        {player: rtg for player, rtg in zip(players, pwr_rtgs)}, 
        opps, 
        {player: c for player, c in zip(players, colors)}
    )

