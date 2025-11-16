import random

piece_score = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "P": 1}
CHECK_MATE = 1000
STALE_MATE = 0
DEPTH = 3

def find_random_smart_move(valid_moves):
    return valid_moves[random.randint(0, len(valid_moves) - 1)]

def find_best_move(gs, valid_moves):
    global next_move
    next_move = None
    random.shuffle(valid_moves)
    find_move_negamax_alpha_beta(gs, valid_moves, DEPTH, -CHECK_MATE, CHECK_MATE, 1 if gs.white_to_move else -1)
    return next_move

def find_best_move_minmax(gs, valid_moves):
    """Wrapper function for easier difficulty - uses min-max algorithm"""
    global next_move
    next_move = None
    random.shuffle(valid_moves)
    find_move_min_max(gs, valid_moves, DEPTH, gs.white_to_move)
    return next_move

def find_move_min_max(gs, valid_moves, depth, white_to_move):
    global next_move
    if depth == 0:
        return score_materials(gs.board)
    if white_to_move:
        max_score = -CHECK_MATE
        for move in valid_moves:
            gs.make_move(move)
            next_moves = gs.get_valid_moves()
            score = find_move_min_max(gs, next_moves, depth - 1, False)
            if score > max_score:
                max_score = score
                if depth == DEPTH:
                    next_move = move
            gs.undo_move()
        return max_score
    else:
        min_score = CHECK_MATE
        for move in valid_moves:
            gs.make_move(move)
            next_moves = gs.get_valid_moves()
            score = find_move_min_max(gs, next_moves, depth - 1, True)
            if score < min_score:
                min_score = score
                if depth == DEPTH:
                    next_move = move
            gs.undo_move()
        return min_score

def find_move_negamax_alpha_beta(gs, valid_moves, depth, alpha, beta, turn_multiplier):
    global next_move
    if depth == 0:
        return turn_multiplier * score_board(gs)
    
    max_score = -CHECK_MATE
    for move in valid_moves:
        gs.make_move(move)
        next_moves = gs.get_valid_moves()
        score = -find_move_negamax_alpha_beta(gs, next_moves, depth - 1, -beta, -alpha, -turn_multiplier)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move
        gs.undo_move()
        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break
    return max_score

def score_board(gs):
    if gs.check_mate:
        if gs.white_to_move:
            return -CHECK_MATE
        else:
            return CHECK_MATE
    elif gs.stale_mate:
        return STALE_MATE

    score = 0
    for row in gs.board:
        for square in row:
            if square[0] == 'w':
                score += piece_score[square[1]]
            elif square[0] == 'b':
                score -= piece_score[square[1]]
    return score

    
def score_materials(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += piece_score[square[1]]
            elif square[0] == 'b':
                score -= piece_score[square[1]]
    return score