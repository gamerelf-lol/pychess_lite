# pychess_lite.py
import random
import json

# Constants for board indices
PLAYER_TO_MOVE = 64
CASTLING_RIGHTS_KINGSIDE_WHITE = 65
CASTLING_RIGHTS_QUEENSIDE_WHITE = 66
CASTLING_RIGHTS_KINGSIDE_BLACK = 67
CASTLING_RIGHTS_QUEENSIDE_BLACK = 68
EN_PASSANT = 69
HALF_MOVE_CLOCK = 70

class Board:
    def __init__(self):
        self._initialize_zobrist()
        self.position_hash_counts = {}
        self.board = None
        self.position_hash = 0

    @classmethod
    def new(cls):
        instance = cls()
        instance._initialize_new_game()
        return instance

    @classmethod
    def load(cls, filename):
        instance = cls()
        instance._load_from_file(filename)
        return instance

    def _initialize_new_game(self):
        self.board = (
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'] +
            ['p'] * 8 +
            [' '] * 32 +
            ['P'] * 8 +
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'] +
            ['w'] + [True, True, True, True] + [None] + [0]
        )
        self.position_hash = self._hash()
        self.position_hash_counts = {self.position_hash: 1}

    def _load_from_file(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        self.board = data['board']
        self.position_hash = data['position_hash']
        self.position_hash_counts = data['position_hash_counts']

    def save(self, filename):
        data = {
            'board': self.board,
            'position_hash': self.position_hash,
            'position_hash_counts': self.position_hash_counts
        }
        with open(filename, 'w') as f:
            json.dump(data, f)

    def _initialize_zobrist(self):
        self.zobrist_table = {}
        pieces = ['P', 'N', 'B', 'R', 'Q', 'K',
                  'p', 'n', 'b', 'r', 'q', 'k']
        self.zobrist_piece = {}
        random.seed(125104875299311)
        for piece in pieces:
            self.zobrist_piece[piece] = [random.getrandbits(64) for _ in range(64)]
        self.zobrist_side = random.getrandbits(64)
        self.zobrist_castling = {
            'K': random.getrandbits(64),
            'Q': random.getrandbits(64),
            'k': random.getrandbits(64),
            'q': random.getrandbits(64)
        }
        self.zobrist_en_passant = [random.getrandbits(64) for _ in range(8)]

    def _hash(self):
        h = 0
        for index in range(64):
            piece = self.board[index]
            if piece != ' ':
                h ^= self.zobrist_piece[piece][index]
        if self.board[PLAYER_TO_MOVE] == 'w':
            h ^= self.zobrist_side
        if self.board[CASTLING_RIGHTS_KINGSIDE_WHITE]:
            h ^= self.zobrist_castling['K']
        if self.board[CASTLING_RIGHTS_QUEENSIDE_WHITE]:
            h ^= self.zobrist_castling['Q']
        if self.board[CASTLING_RIGHTS_KINGSIDE_BLACK]:
            h ^= self.zobrist_castling['k']
        if self.board[CASTLING_RIGHTS_QUEENSIDE_BLACK]:
            h ^= self.zobrist_castling['q']
        if self.board[EN_PASSANT] is not None:
            target_square = self.board[EN_PASSANT]
            file = ord(target_square[0]) - ord('a')
            h ^= self.zobrist_en_passant[file]
        return h
    
    def player_to_move(self):
        return self.board[PLAYER_TO_MOVE]

    def white_to_move(self):
        return self.player_to_move() == 'w'

    def black_to_move(self):
        return self.player_to_move() == 'b'

    def legal_moves(self):
        if self.board is None:
            raise ValueError("Engine not initialized. Call new() or load() before using this method.")
        turn = self.player_to_move()
        legal_moves = []
        starting_coordinates = [
            i for i, piece in enumerate(self.board[:64])
            if (turn == 'w' and piece.isupper()) or (turn == 'b' and piece.islower())
        ]
        opponent_moves = self.dangerous_squares()
        en_passant_move = self.board[EN_PASSANT]
        en_passant_target = self._en_passant_target_index()
        for start in starting_coordinates:
            piece = self.board[start]
            if piece.upper() == 'P':
                direction = -1 if piece.isupper() else 1
                forward_one = start + (direction * 8)
                if 0 <= forward_one < 64 and self.board[forward_one] == ' ':
                    if (piece.isupper() and forward_one < 8) or (piece.islower() and forward_one >= 56):
                        for promo_piece in ['Q', 'R', 'B', 'N']:
                            promo = promo_piece.lower() if piece.islower() else promo_piece
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(forward_one)}{promo}')
                    else:
                        legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(forward_one)}')
                    starting_rank = 6 if piece.isupper() else 1
                    if (start // 8 == starting_rank):
                        forward_two = start + (direction * 16)
                        if self.board[forward_two] == ' ' and self.board[forward_one] == ' ':
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(forward_two)}')
                for dx in [-1, 1]:
                    x = (start % 8) + dx
                    y = (start // 8) + direction
                    if 0 <= x < 8 and 0 <= y < 8:
                        target = y * 8 + x
                        target_piece = self.board[target]
                        if target_piece != ' ' and (target_piece.islower() if piece.isupper() else target_piece.isupper()):
                            if (piece.isupper() and target < 8) or (piece.islower() and target >= 56):
                                for promo_piece in ['Q', 'R', 'B', 'N']:
                                    promo = promo_piece.lower() if piece.islower() else promo_piece
                                    legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}{promo}')
                            else:
                                legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
                        elif self.index_to_square(target) == en_passant_move:
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
            elif piece.upper() == 'N':
                knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                (1, -2), (1, 2), (2, -1), (2, 1)]
                x = start % 8
                y = start // 8
                for dx, dy in knight_moves:
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        target_piece = self.board[target]
                        if target_piece == ' ' or (
                            target_piece.islower() if piece.isupper() else target_piece.isupper()
                        ):
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
            elif piece.upper() in ['B', 'R', 'Q']:
                directions = []
                if piece.upper() == 'B':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                elif piece.upper() == 'R':
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                elif piece.upper() == 'Q':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                                  (-1, 0), (1, 0), (0, -1), (0, 1)]
                x = start % 8
                y = start // 8
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    while 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        target_piece = self.board[target]
                        legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
                        if target_piece == ' ':
                            pass
                        elif (target_piece.islower() if piece.isupper() else target_piece.isupper()):
                            break
                        else:
                            break
                        nx += dx
                        ny += dy
            elif piece.upper() == 'K':
                x = start % 8
                y = start // 8
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1),
                               (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        target_piece = self.board[target]
                        if (target_piece == ' ' or
                            (target_piece.islower() if piece.isupper() else target_piece.isupper())):
                            target_square = self.index_to_square(target)
                            if target_square not in opponent_moves:
                                legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
                rights = self.castling_rights()
                king_side_square = start + 2
                queen_side_square = start - 2
                if rights['king_side']:
                    legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(king_side_square)}')
                if rights['queen_side']:
                    legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(queen_side_square)}')
        safe_moves = []
        for move in legal_moves:
            temp_board = self.board.copy()
            temp_hash = self.position_hash
            self.move(move, test=True, temp_board=temp_board)
            original_board = self.board
            self.board = temp_board
            if not self.check():
                safe_moves.append(move)
            self.board = original_board
            self.position_hash = temp_hash
        return safe_moves

    def check(self):
        king_char = 'K' if self.white_to_move() else 'k'
        try:
            king_pos = self.board.index(king_char)
        except ValueError:
            return True
        king_square = self.index_to_square(king_pos)
        opponent_moves = self.dangerous_squares()
        return king_square in opponent_moves

    def castling_rights(self):
        rights = {'king_side': False, 'queen_side': False}
        king_char = 'K' if self.white_to_move() else 'k'
        try:
            king_pos = self.board.index(king_char)
        except ValueError:
            return rights
        opponent_moves = self.dangerous_squares()
        king_square = self.index_to_square(king_pos)
        if self.player_to_move() == 'w':
            if self.board[CASTLING_RIGHTS_KINGSIDE_WHITE]:
                if self.board[63] == 'R':
                    if self.board[61] == ' ' and self.board[62] == ' ':
                        if (king_square not in opponent_moves and
                            self.index_to_square(king_pos + 1) not in opponent_moves and
                            self.index_to_square(king_pos + 2) not in opponent_moves):
                            rights['king_side'] = True
            if self.board[CASTLING_RIGHTS_QUEENSIDE_WHITE]:
                if self.board[56] == 'R':
                    if self.board[57] == ' ' and self.board[58] == ' ' and self.board[59] == ' ':
                        if (king_square not in opponent_moves and
                            self.index_to_square(king_pos - 1) not in opponent_moves and
                            self.index_to_square(king_pos - 2) not in opponent_moves):
                            rights['queen_side'] = True
        else:
            if self.board[CASTLING_RIGHTS_KINGSIDE_BLACK]:
                if self.board[7] == 'r':
                    if self.board[5] == ' ' and self.board[6] == ' ':
                        if (king_square not in opponent_moves and
                            self.index_to_square(king_pos + 1) not in opponent_moves and
                            self.index_to_square(king_pos + 2) not in opponent_moves):
                            rights['king_side'] = True
            if self.board[CASTLING_RIGHTS_QUEENSIDE_BLACK]:
                if self.board[0] == 'r':
                    if self.board[1] == ' ' and self.board[2] == ' ' and self.board[3] == ' ':
                        if (king_square not in opponent_moves and
                            self.index_to_square(king_pos - 1) not in opponent_moves and
                            self.index_to_square(king_pos - 2) not in opponent_moves):
                            rights['queen_side'] = True
        return rights

    def move(self, move, test=False, temp_board=None):
        board = temp_board if temp_board is not None else self.board
        start, end = move[:2], move[2:4]
        promotion_piece = move[4] if len(move) > 4 else ''
        start_index = self.square_to_index(start)
        end_index = self.square_to_index(end)
        moving_piece = board[start_index]
        target_piece = board[end_index]
        if not test and move not in self.legal_moves():
            raise ValueError(f"Illegal move: {move}")
        if moving_piece.upper() == 'K' and abs(start_index - end_index) == 2:
            if end_index > start_index:
                rook_start = start_index + 3
                rook_end = start_index + 1
            else:
                rook_start = start_index - 4
                rook_end = start_index - 1
            rook_piece = board[rook_start]
            board[start_index] = ' '
            board[end_index] = moving_piece
            board[rook_start] = ' '
            board[rook_end] = rook_piece
            if moving_piece.isupper():
                board[CASTLING_RIGHTS_KINGSIDE_WHITE] = False  
                board[CASTLING_RIGHTS_QUEENSIDE_WHITE] = False  
            else:
                board[CASTLING_RIGHTS_KINGSIDE_BLACK] = False  
                board[CASTLING_RIGHTS_QUEENSIDE_BLACK] = False  
            if not test:
                self.position_hash ^= self.zobrist_piece[moving_piece][start_index]
                self.position_hash ^= self.zobrist_piece[rook_piece][rook_start]
                self.position_hash ^= self.zobrist_piece[moving_piece][end_index]
                self.position_hash ^= self.zobrist_piece[rook_piece][rook_end]
                if moving_piece.isupper():
                    if board[CASTLING_RIGHTS_KINGSIDE_WHITE]:
                        self.position_hash ^= self.zobrist_castling['K']
                        board[CASTLING_RIGHTS_KINGSIDE_WHITE] = False
                    if board[CASTLING_RIGHTS_QUEENSIDE_WHITE]:
                        self.position_hash ^= self.zobrist_castling['Q']
                        board[CASTLING_RIGHTS_QUEENSIDE_WHITE] = False
                else:
                    if board[CASTLING_RIGHTS_KINGSIDE_BLACK]:
                        self.position_hash ^= self.zobrist_castling['k']
                        board[CASTLING_RIGHTS_KINGSIDE_BLACK] = False
                    if board[CASTLING_RIGHTS_QUEENSIDE_BLACK]:
                        self.position_hash ^= self.zobrist_castling['q']
                        board[CASTLING_RIGHTS_QUEENSIDE_BLACK] = False
        else:
            en_passant_move = board[EN_PASSANT]
            en_passant_target = self._en_passant_target_index()
            if moving_piece.upper() == 'P' and end_index == en_passant_target:
                if moving_piece.isupper():
                    capture_index = end_index + 8
                else:
                    capture_index = end_index - 8
                captured_pawn = board[capture_index]
                if captured_pawn.upper() != 'P':
                    raise ValueError(f"En passant capture failed: No pawn to capture at {self.index_to_square(capture_index)}")
                board[capture_index] = ' '
                if not test:
                    self.position_hash ^= self.zobrist_piece[captured_pawn][capture_index]
            board[start_index] = ' '
            if promotion_piece:
                promoted_piece = promotion_piece.upper() if moving_piece.isupper() else promotion_piece.lower()
                board[end_index] = promoted_piece
            else:
                board[end_index] = moving_piece
            if moving_piece.upper() == 'R':
                if moving_piece.isupper():
                    if start_index == 56:
                        if board[CASTLING_RIGHTS_QUEENSIDE_WHITE]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['Q']
                            board[CASTLING_RIGHTS_QUEENSIDE_WHITE] = False
                    elif start_index == 63:
                        if board[CASTLING_RIGHTS_KINGSIDE_WHITE]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['K']
                            board[CASTLING_RIGHTS_KINGSIDE_WHITE] = False
                else:
                    if start_index == 0:
                        if board[CASTLING_RIGHTS_QUEENSIDE_BLACK]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['q']
                            board[CASTLING_RIGHTS_QUEENSIDE_BLACK] = False
                    elif start_index == 7:
                        if board[CASTLING_RIGHTS_KINGSIDE_BLACK]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['k']
                            board[CASTLING_RIGHTS_KINGSIDE_BLACK] = False
            if moving_piece.upper() == 'P' and abs(start_index - end_index) == 16:
                if moving_piece.isupper():
                    to_square = self.index_to_square(start_index - 8)
                else:
                    to_square = self.index_to_square(start_index + 8)
                if not test and board[EN_PASSANT] is not None:
                    previous_target = board[EN_PASSANT]
                    previous_file = ord(previous_target[0]) - ord('a')
                    self.position_hash ^= self.zobrist_en_passant[previous_file]
                board[EN_PASSANT] = to_square
                if not test:
                    file = ord(to_square[0]) - ord('a')
                    self.position_hash ^= self.zobrist_en_passant[file]
            else:
                if not test and board[EN_PASSANT] is not None:
                    previous_target = board[EN_PASSANT]
                    previous_file = ord(previous_target[0]) - ord('a')
                    self.position_hash ^= self.zobrist_en_passant[previous_file]
                board[EN_PASSANT] = None
            if not test:
                self.position_hash ^= self.zobrist_piece[moving_piece][start_index]
                if target_piece != ' ' and not (moving_piece.upper() == 'P' and end_index == en_passant_target):
                    self.position_hash ^= self.zobrist_piece[target_piece][end_index]
                self.position_hash ^= self.zobrist_piece[board[end_index]][end_index]
                if moving_piece.upper() == 'K':
                    if moving_piece.isupper():
                        if board[CASTLING_RIGHTS_KINGSIDE_WHITE]:
                            self.position_hash ^= self.zobrist_castling['K']
                            board[CASTLING_RIGHTS_KINGSIDE_WHITE] = False
                        if board[CASTLING_RIGHTS_QUEENSIDE_WHITE]:
                            self.position_hash ^= self.zobrist_castling['Q']
                            board[CASTLING_RIGHTS_QUEENSIDE_WHITE] = False
                    else:
                        if board[CASTLING_RIGHTS_KINGSIDE_BLACK]:
                            self.position_hash ^= self.zobrist_castling['k']
                            board[CASTLING_RIGHTS_KINGSIDE_BLACK] = False
                        if board[CASTLING_RIGHTS_QUEENSIDE_BLACK]:
                            self.position_hash ^= self.zobrist_castling['q']
                            board[CASTLING_RIGHTS_QUEENSIDE_BLACK] = False
        if not test:
            if moving_piece.upper() == 'P' or target_piece != ' ' or promotion_piece:
                board[HALF_MOVE_CLOCK] = 0
            else:
                board[HALF_MOVE_CLOCK] += 1
            board[PLAYER_TO_MOVE] = 'b' if board[PLAYER_TO_MOVE] == 'w' else 'w'
            self.position_hash ^= self.zobrist_side
            count = self.position_hash_counts.get(self.position_hash, 0)
            self.position_hash_counts[self.position_hash] = count + 1

        return board

    def square_to_index(self, square):
        file = ord(square[0]) - ord('a')
        rank = 8 - int(square[1])
        return rank * 8 + file

    def index_to_square(self, index):
        file = index % 8
        rank = 8 - (index // 8)
        return f'{chr(file + ord("a"))}{rank}'

    def dangerous_squares(self):
        opponent_moves = set()
        opponent_turn = 'b' if self.player_to_move() == 'w' else 'w'
        starting_coordinates = [
            i for i, piece in enumerate(self.board[:64])
            if (opponent_turn == 'w' and piece.isupper()) or (opponent_turn == 'b' and piece.islower())
        ]
        for start in starting_coordinates:
            piece = self.board[start]
            if piece.upper() == 'P':
                direction = -1 if piece.isupper() else 1
                for dx in [-1, 1]:
                    x = (start % 8) + dx
                    y = (start // 8) + direction
                    if 0 <= x < 8 and 0 <= y < 8:
                        target_square = self.index_to_square(y * 8 + x)
                        opponent_moves.add(target_square)
            elif piece.upper() == 'N':
                knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), 
                                (1, -2), (1, 2), (2, -1), (2, 1)]
                x = start % 8
                y = start // 8
                for dx, dy in knight_moves:
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target_square = self.index_to_square(ny * 8 + nx)
                        opponent_moves.add(target_square)
            elif piece.upper() in ['B', 'R', 'Q']:
                directions = []
                if piece.upper() == 'B':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                elif piece.upper() == 'R':
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                elif piece.upper() == 'Q':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), 
                                  (-1, 0), (1, 0), (0, -1), (0, 1)]
                x = start % 8
                y = start // 8
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    while 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        target_square = self.index_to_square(target)
                        opponent_moves.add(target_square)
                        if self.board[target] != ' ':
                            break
                        nx += dx
                        ny += dy
            elif piece.upper() == 'K':
                x = start % 8
                y = start // 8
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), 
                               (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target_square = self.index_to_square(ny * 8 + nx)
                        opponent_moves.add(target_square)
        return opponent_moves

    def insufficient_material(self):
        white_pieces = []
        black_pieces = []
        for index, piece in enumerate(self.board[:64]):
            if piece == ' ' or piece.upper() == 'K':
                continue
            if piece.isupper():
                white_pieces.append((piece, index))
            else:
                black_pieces.append((piece, index))
        minor_pieces = ['N', 'B']
        if not white_pieces and not black_pieces:
            return True
        if (len(white_pieces) == 1 and white_pieces[0][0].upper() in minor_pieces and not black_pieces) or \
           (len(black_pieces) == 1 and black_pieces[0][0].upper() in minor_pieces and not white_pieces):
            return True
        if len(white_pieces) == 1 and len(black_pieces) == 1:
            if white_pieces[0][0].upper() == 'B' and black_pieces[0][0].upper() == 'B':
                white_square_color = (white_pieces[0][1] // 8 + white_pieces[0][1] % 8) % 2
                black_square_color = (black_pieces[0][1] // 8 + black_pieces[0][1] % 8) % 2
                if white_square_color == black_square_color:
                    return True
        return False

    def fifty_move_rule(self):
        return self.board[HALF_MOVE_CLOCK] >= 100

    def stalemate(self):
        if not self.legal_moves():
            return not self.check()
        return False

    def three_fold_repetition(self):
        return self.position_hash_counts.get(self.position_hash, 0) >= 3

    def checkmate(self):
        if self.check():
            return not self.legal_moves()
        return False

    def en_passant(self):
        return self.board[EN_PASSANT]

    def _en_passant_target_index(self):
        if self.board[EN_PASSANT] is None:
            return -1
        target_square = self.board[EN_PASSANT]
        return self.square_to_index(target_square)
