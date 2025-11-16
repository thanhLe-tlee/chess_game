class GameState:
    def __init__(self):
        # Initialize the chess board with 8x8 grid and pieces
        # 'b' = black, 'w' = white
        # 'R' = Rook, 'N' = Knight, 'B' = Bishop, 'Q' = Queen, 'K' = King, 'P' = 
        # '--' = empty square
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.move_functions = {'P': self.get_pawn_moves, 'R': self.get_rook_moves,
                               'N': self.get_knight_moves, 'B': self.get_bishop_moves,
                               'Q': self.get_queen_moves, 'K': self.get_king_moves}
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.check_mate = False
        self.stale_mate = False
        self.is_in_check = False
        self.en_passant_possible = ()
        self.pins = []
        self.checks = []
        self.current_castle_right = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castle_right.wks, self.current_castle_right.bks, self.current_castle_right.wqs, self.current_castle_right.bqs)]
        self.position_history = []  # Track positions for threefold repetition
        self.draw_by_repetition = False

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move # its black's turn to move
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)
        
        if move.is_pawn_promotion:
            promotion_piece = move.promotion_choice if move.promotion_choice else 'Q'
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + promotion_piece

        if move.is_en_passant_move:
            self.board[move.start_row][move.end_col] = "--"
        
        if move.piece_moved[1] == 'P' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row)//2, move.start_col)
        else:
            self.en_passant_possible = ()

        if move.is_castle_move:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        self.update_castle_rights(move)
        self.castle_rights_log.append(CastleRights(self.current_castle_right.wks, self.current_castle_right.bks, self.current_castle_right.wqs, self.current_castle_right.bqs))
        
        # Add current position to history for threefold repetition check
        self.position_history.append(self.get_board_hash())
        
        # Check for threefold repetition
        if self.position_history.count(self.position_history[-1]) >= 3:
            self.draw_by_repetition = True

    def undo_move(self):
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move # reverse back to white move
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            if move.is_en_passant_move:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured
                self.en_passant_possible = (move.end_row, move.end_col)
            if move.piece_moved[1] == 'P' and abs(move.start_row - move.end_row) == 2:
                self.en_passant_possible = ()
            
            self.castle_rights_log.pop()
            self.current_castle_right = self.castle_rights_log[-1]
            
            # Remove position from history
            if self.position_history:
                self.position_history.pop()
            self.draw_by_repetition = False

            if move.is_castle_move:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = "--"
                else:
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = "--"
        
            self.check_mate = False
            self.stale_mate = False

    def update_castle_rights(self, move):
        if move.piece_moved == 'wK':
            self.current_castle_right.wks = False
            self.current_castle_right.wqs = False
        elif move.piece_moved == 'bK':
            self.current_castle_right.bks = False
            self.current_castle_right.bqs = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0: # left rook
                    self.current_castle_right.wqs = False
                elif move.start_col == 7: # right rook
                    self.current_castle_right.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0: # left rook
                    self.current_castle_right.bqs = False
                elif move.start_col == 7: # right rook
                    self.current_castle_right.bks = False

    def get_valid_moves(self):
        temp_en_passant_possible = self.en_passant_possible
        temp_castle_rights = CastleRights(self.current_castle_right.wks, self.current_castle_right.bks, self.current_castle_right.wqs, self.current_castle_right.bqs)
        moves = []
        self.is_in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.is_in_check:
            if len(self.checks) == 1: 
                moves = self.get_all_possible_moves()
                check = self.checks[0] 
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col] 
                valid_squares = [] 
                if piece_checking[1] == 'N': 
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break
                for i in range(len(moves)-1, -1, -1):
                    if moves[i].piece_moved[1] != 'K':
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:
                self.get_king_moves(king_row, king_col, moves)
            
            if len(moves) == 0:
                self.check_mate = True
                return moves
        else: 
            # Get all moves and add castling moves when not in check
            moves = self.get_all_possible_moves()
            if self.white_to_move:
                self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        self.en_passant_possible = temp_en_passant_possible
        self.current_castle_right = temp_castle_rights
        return moves
    
    def check_for_pins_and_checks(self):
        pins = []
        checks = []
        is_in_check = False
        if self.white_to_move:
            enemy_color = 'b'
            ally_color = 'w'
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = 'w'
            ally_color = 'b'
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()
            for i in range(1, 8):
                end_row = start_row + d[0] * i
                end_col = start_col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != 'K':
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:
                            break
                    elif end_piece[0] == enemy_color:
                        type = end_piece[1]
                        if (0 <= j <= 3 and type == 'R') or \
                            (4 <= j <= 7 and type == 'B') or \
                            (i == 1 and type == 'P' and ((enemy_color == 'w' and 6 <= j <= 7) or (enemy_color == 'b' and 4 <= j <=5))) or \
                            (type == 'Q') or (i == 1 and type == 'K'):
                            if possible_pin == ():
                                is_in_check = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:
                                pins.append(possible_pin)
                                break
                        else: 
                            break
                else:
                    break

        knight_moves = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
        for m in knight_moves:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == 'N':
                    is_in_check = True
                    checks.append((end_row, end_col, m[0], m[1]))
        return is_in_check, pins, checks

    def is_in_check(self):
        if self.white_to_move:
            return self.square_under_attack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.square_under_attack(self.black_king_location[0], self.black_king_location[1])

    def square_under_attack(self, r, c):
        self.white_to_move = not self.white_to_move
        opponent_moves = self.get_all_possible_moves()
        self.white_to_move = not self.white_to_move
        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def get_all_possible_moves(self):
        possible_moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](r, c, possible_moves)
        return possible_moves

    def get_pawn_moves(self, r, c, moves):
        pieced_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                pieced_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            if self.board[r - 1][c] == "--":
                if not pieced_pinned or pin_direction == (-1, 0):
                    moves.append(Move((r, c), (r-1, c), self.board))
                    if r == 6 and self.board[r-2][c] == "--":
                        moves.append(Move((r, c), (r-2, c), self.board))
            if c - 1 >= 0:
                if self.board[r-1][c-1][0] == 'b':
                    if not pieced_pinned or pin_direction == (-1, -1):
                        moves.append(Move((r, c), (r - 1, c - 1), self.board))
                elif (self.en_passant_possible == (r - 1, c - 1)):
                        moves.append(Move((r, c), (r - 1, c - 1), self.board, is_en_passant_move=True))
            if c + 1 <= 7:
                if self.board[r-1][c+1][0] == 'b':
                    if not pieced_pinned or pin_direction == (-1, 1):
                        moves.append(Move((r, c), (r - 1, c + 1), self.board))
                elif (self.en_passant_possible == (r - 1, c + 1)):
                        moves.append(Move((r, c), (r - 1, c + 1), self.board, is_en_passant_move=True))
        else:
            if self.board[r + 1][c] == "--":
                if not pieced_pinned or pin_direction == (1, 0):
                    moves.append(Move((r, c), (r + 1, c), self.board))
                    if r == 1 and self.board[r + 2][c] == "--":
                        moves.append(Move((r, c), (r + 2, c), self.board))
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == 'w':
                    if not pieced_pinned or pin_direction == (1, -1):
                        moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (self.en_passant_possible == (r + 1, c - 1)):
                        moves.append(Move((r, c), (r + 1, c - 1), self.board, is_en_passant_move=True))
            if c + 1 <= 7:
                if self.board[r + 1][c + 1][0] == 'w':
                    if not pieced_pinned or pin_direction == (1, 1):
                        moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (self.en_passant_possible == (r + 1, c + 1)):
                        moves.append(Move((r, c), (r + 1, c + 1), self.board, is_en_passant_move=True))

    def get_rook_moves(self, r, c, moves):
        pieced_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                pieced_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)] # up, left, down, right
        enemy_color = 'b' if self.white_to_move else 'w'
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not pieced_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_knight_moves(self, r, c, moves):
        pieced_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                pieced_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)] # 8 possible moves
        ally_color = 'w' if self.white_to_move else 'b'
        for k in knight_moves:
            end_row = r + k[0]
            end_col = c + k[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if not pieced_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        pieced_pinned = False
        pin_direction = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                pieced_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)] # 4 diagonals
        enemy_color = 'b' if self.white_to_move else 'w'
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not pieced_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def get_queen_moves(self, r, c, moves):
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        row_move = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_move = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = 'w' if self.white_to_move else 'b'
        for i in range(8):
            end_row = r + row_move[i]
            end_col = c + col_move[i]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    if ally_color == 'w':
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    is_in_check, pins, checks = self.check_for_pins_and_checks()
                    if not is_in_check:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    if ally_color == 'w':
                        self.white_king_location = (r, c)
                    else:
                        self.black_king_location = (r, c)
    
    def get_castle_moves(self, r, c, moves):
        if self.square_under_attack(r, c):
            return 
        if (self.white_to_move and self.current_castle_right.wks) or (not self.white_to_move and self.current_castle_right.bks):
            self.get_king_side_castle_moves(r, c, moves)
        if (self.white_to_move and self.current_castle_right.wqs) or (not self.white_to_move and self.current_castle_right.bqs):
            self.get_queen_side_castle_moves(r, c, moves)

    def get_king_side_castle_moves(self, r, c, moves):
        if (self.board[r][c+1] == "--" and self.board[r][c+2] == "--"):
            if not self.square_under_attack(r, c+1) and not self.square_under_attack(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, is_castle_move=True))

    def get_queen_side_castle_moves(self, r, c, moves):
        if (self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--"):
            if not self.square_under_attack(r, c-1) and not self.square_under_attack(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, is_castle_move=True))
    
    def get_board_hash(self):
        """Create a hashable representation of the current board position"""
        # Convert board to a tuple of tuples (immutable and hashable)
        board_tuple = tuple(tuple(row) for row in self.board)
        # Include whose turn it is and castling rights in the hash
        return (board_tuple, self.white_to_move, 
                self.current_castle_right.wks, self.current_castle_right.wqs,
                self.current_castle_right.bks, self.current_castle_right.bqs,
                self.en_passant_possible)

class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs
    


class Move():
    rank_to_rows = {"1":7, "2":6, "3":5, "4":4,
                    "5":3, "6":2, "7":1, "8":0}
    rows_to_rank = {v: k for k, v in rank_to_rows.items()}

    file_to_cols = {"a":0, "b":1, "c":2, "d":3,
                    "e":4, "f":5, "g":6, "h":7}
    cols_to_file = {v: k for k, v in file_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_en_passant_move = False, is_castle_move = False, promotion_choice=None):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.is_pawn_promotion = (self.piece_moved == 'wP' and self.end_row == 0) or (self.piece_moved == 'bP' and self.end_row == 7)
        self.promotion_choice = promotion_choice

        # self.is_en_passant_move = (self.piece_moved[1] == 'P' and (self.end_row, self.end_col) == en_passant_possible)
        self.is_en_passant_move = is_en_passant_move
        if self.is_en_passant_move:
            if self.piece_moved[0] == 'w':
                self.piece_captured = 'bP'
            else:
                self.piece_captured = 'wP'
        
        self.is_castle_move = is_castle_move

        self.move_id = (self.start_row * 1000 + self.start_col * 100 +
                        self.end_row * 10 + self.end_col)
        # print(self.move_id)
    
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False
    
    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)
    def get_rank_file(self, r, c):
        return self.cols_to_file[c] + self.rows_to_rank[r]