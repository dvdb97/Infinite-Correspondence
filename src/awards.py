import chess

from apis import init_lichess_api

from typing import List, Dict


def get_material(board: chess.Board):
    mat_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

    w_mat = 0
    b_mat = 0

    for ptype in chess.PIECE_TYPES:
        for _ in board.pieces(ptype, chess.WHITE):
            w_mat += mat_values[ptype]

        for _ in board.pieces(ptype, chess.BLACK):
            b_mat += mat_values[ptype]

    return w_mat, b_mat


def compute_compensation(game: Dict):
    moves = game['moves'].split(' ')
    evals = game['analysis']

    board = chess.Board()

    w_comp = 0
    b_comp = 0
    n_moves = 0
    
    for idx, (move, eval) in enumerate(zip(moves, evals)):
        board.push_san(move)

        w_mat, b_mat = get_material(board)
        mat_diff = w_mat - b_mat

        if 'eval' in eval:
            eval = eval['eval']
        elif 'mate' in eval:
            eval = eval['mate']

        if mat_diff < 0 and eval > 0 and idx % 2 == 0:
            w_comp += 1
        
        if mat_diff > 0 and eval < 0 and idx % 2 == 1:
            b_comp += 1

        n_moves += idx % 2

    return round(100 * w_comp / n_moves), round(100 * b_comp / n_moves)


if __name__ == '__main__':
    client = init_lichess_api()

    games = client.games.export_multi('PxLKlcpt', 'uzk5VWkz', 'OSLkW39l', evals=True, opening=True)

    for game in games:
        print(game['id'])
        w_comp, b_comp = compute_compensation(game)

        print(f'{w_comp*100}% vs {b_comp*100}%')
