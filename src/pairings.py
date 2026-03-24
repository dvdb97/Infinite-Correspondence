import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

from enum import Enum
from typing import List, Dict, Set
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


def get_active_pairings(df: pd.DataFrame, players) -> Set[Set[str]]:
    """_summary_

    Args:
        df (pd.DataFrame): _description_
        players (_type_): _description_

    Returns:
        Set[Set[str]]: _description_
    """
    df_filtered = df[(df['White'].isin(players) | df['Black'].isin(players))]
    df_filtered = df_filtered[df_filtered['Results'].isin({'game', None, ''})]

    active_games = {(row['White'], row['Black']) for _, row in df_filtered.iterrows()}

    return active_games


def get_k_recent_opponents(df: pd.DataFrame, players, k=5) -> Dict[str, List[str]]:
    """Extracts the recent k opponents for each players from the spreadsheet.

    Args:
        spreadsheet (_type_): The speadsheet to load the data from.
        players (_type_): The list of players to get the data for.
        k (int, optional): The number of recent games to consider. Defaults to 5. 

    Returns:
        Dict[str, List[str]]: Returns a dict containing the list of recent players for each
        player.
    """
    df_filtered = df[(df['White'].isin(players) | df['Black'].isin(players))]
    df_sorted = df_filtered.sort_values(by='Round', ascending=False)

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


def get_recent_game(df, player_a, player_b):
    players = { player_a, player_b }
    df_filtered = df[(df['White'].isin(players) & df['Black'].isin(players))]
    df_sorted = df_filtered.sort_values(by='Start_Date', ascending=False)

    if len(df_sorted) == 0:
        return None
    
    return df_sorted['White'].iloc[0], df_sorted['Black'].iloc[0]


def plot_pairings_graph(G, pairing_players=None):
    # Create a mapping of indices to player names if provided
    if pairing_players:
        node_labels = {i: pairing_players[i] for i in G.nodes()}
        edge_labels = {(a, b): weight for a, b, weight in G.edges(data='weight') if weight < 100}
    else:
        edge_labels = {(a, b): weight for a, b, weight in G.edges(data='weight') if weight < 100}
        node_labels = {node: node for node in G.nodes()}

    pos = nx.circular_layout(G)
    nx.draw_networkx_nodes(G, pos)
    nx.draw_networkx_labels(G, pos, labels=node_labels)
    nx.draw_networkx_edges(G, pos, edgelist=[(a, b) for a, b, weight in G.edges(data='weight') if weight < 100])
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_color='black',
        font_size=5
    )
    plt.show()


def generate_pairings(df: pd.DataFrame, players: List[str], rtgs: Dict[str, float], col_pref: Dict[str, ColorPref], verbose: bool = True, exclude_pairings: set = None):
    """Generates pairings for the given players based on their ratings, recent opponents and color
    preferences. It constraints the potential pairings to not include pairings that have recently
    occured. With odd numbers, one player will receive a 2nd pairing.

    Args:
        players (List[str]): The players to pair.
        rtgs (Dict[str, float]): The player's ratings.
        cols_pref (Dict[str, int]): The color preference for each player.
        verbose (bool): Whether to print debug info and show graph. Defaults to True.
        exclude_pairings (set): Set of tuples representing pairings to exclude (e.g., from previous round).
    """
    if exclude_pairings is None:
        exclude_pairings = set()
    
    pairing_players = players.copy()
    double_pairing_player = None
    
    # Handle odd number of players
    if len(players) % 2 != 0:
        if verbose:
            print(f"\nOdd number of players ({len(players)}). One player will receive a 2nd pairing.")
            print(f"Available players: {', '.join(players)}")
        
        while True:
            player_input = input(f"Enter the username of the player who should receive a 2nd pairing: ").lower()
            if player_input in players:
                double_pairing_player = player_input
                # Add the player twice to the list so they get paired twice
                pairing_players.append(double_pairing_player)
                if verbose:
                    print(f"{double_pairing_player} will receive a 2nd pairing\n")
                break
            else:
                print(f"Player '{player_input}' not found. Please enter a valid username.")
    
    assert len(pairing_players) % 2 == 0, "Number of pairing players must be even!"

    recent_k_opps = get_k_recent_opponents(df, players)
    if verbose:
        print(recent_k_opps)

    active_games = get_active_pairings(df, players)
    if verbose:
        print(active_games)

    G = nx.Graph()
    G.add_nodes_from(range(len(pairing_players)))  # Use indices instead of player names

    # Connect two players with an edge iff they don't prefer the same color and haven't been matched recently.
    for i, j in combinations(range(len(pairing_players)), 2):
        a = pairing_players[i]
        b = pairing_players[j]
        
        # Prevent a player from being paired with themselves (if they have 2 slots)
        if a == b:
            continue
        
        # Prevent pairings that should be excluded (e.g., from previous round)
        pairing = frozenset([a, b])
        if pairing in exclude_pairings:
            continue
            
        if b not in recent_k_opps[a] or a not in recent_k_opps[b]:
            G.add_edge(i, j, weight=abs(rtgs[a]-rtgs[b]))

    # Compute the pairings with a min weight matching on the created graph.
    pairings_indices = nx.algorithms.matching.min_weight_matching(G)
    
    # Convert indices back to player names
    pairings = [(pairing_players[i], pairing_players[j]) for i, j in pairings_indices]

    # pretty print the pairings.
    for a, b in pairings:
        recent_game = get_recent_game(df, a, b)

        if recent_game != None:
            if recent_game[0] == a:
                print(f'@{ b } vs @{ a }')
            else:
                print(f'@{ a } vs @{ b }')
        elif col_pref[a] <= col_pref[b]:
            print(f'@{ a } vs @{ b }')
        else:
            print(f'@{ b } vs @{ a }')

    if verbose:
        plot_pairings_graph(G, pairing_players)
    
    return pairings


def generate_double_round_pairings(df: pd.DataFrame, players: List[str], rtgs: Dict[str, float], col_pref: Dict[str, ColorPref]):
    """Generates pairings for a double round, with round 2 avoiding round 1 pairings.

    Args:
        df (pd.DataFrame): The games dataframe.
        players (List[str]): The players to pair.
        rtgs (Dict[str, float]): The player's ratings.
        col_pref (Dict[str, ColorPref]): The color preference for each player.
    """
    print("=" * 50)
    print("ROUND 1")
    print("=" * 50)
    pairings_round1 = generate_pairings(df, players, rtgs, col_pref, verbose=False)
    
    # Convert pairings to a set of frozensets for comparison (order doesn't matter)
    exclude_pairings = {frozenset([a, b]) for a, b in pairings_round1}
    
    # Ask user to exclude players from Round 2
    print("\n" + "=" * 50)
    print("ROUND 2 - PLAYER EXCLUSIONS")
    print("=" * 50)
    exclusion_input = input("Enter comma-separated list of players to exclude from Round 2 (or press Enter to include all): ").strip()
    
    excluded_players = set()
    if exclusion_input:
        excluded_players = {p.strip().lower() for p in exclusion_input.split(',')}
    
    players_for_round2 = [p for p in players if p not in excluded_players]
    
    print("\n" + "=" * 50)
    print("ROUND 2")
    print("=" * 50)
    pairings_round2 = generate_pairings(df, players_for_round2, rtgs, col_pref, verbose=False, exclude_pairings=exclude_pairings)


if __name__ == '__main__':
    spreadsheet = init_gspread_api()

    df, _ = download_as_dataframe(spreadsheet, 'Pairing_Maker', 'PairingMaker')

    players = [player.lower() for player in df['Player']]
    pwr_rtgs = pd.to_numeric(df['Power Score']) 
    colors = pd.to_numeric(df['Color Score'])

    df, _ = download_as_dataframe(spreadsheet, 'RawData', 'RawData')
    df = df.set_index(['ID'])
    df['Round'] = pd.to_numeric(df['Round'])

    # Uncomment the line below if a double round is needed
    # generate_double_round_pairings(
    #     df,
    #     players, 
    #     {player: rtg for player, rtg in zip(players, pwr_rtgs)}, 
    #     {player: c for player, c in zip(players, colors)}
    # )
    
    # For single round, uncomment the line below and comment out the generate_double_round_pairings call
    generate_pairings(
        df,
        players, 
        {player: rtg for player, rtg in zip(players, pwr_rtgs)}, 
        {player: c for player, c in zip(players, colors)}
    )

