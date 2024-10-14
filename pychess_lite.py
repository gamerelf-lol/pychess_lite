import random
import json

class Engine:
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
            ['w'] + [True, True, True, True] + [-1] + [0]
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
        if self.board[64] == 'w':
            h ^= self.zobrist_side
        if self.board[65]:
            h ^= self.zobrist_castling['K']
        if self.board[66]:
            h ^= self.zobrist_castling['Q']
        if self.board[67]:
            h ^= self.zobrist_castling['k']
        if self.board[68]:
            h ^= self.zobrist_castling['q']
        if self.board[69] != -1:
            file = self.board[69] % 8
            h ^= self.zobrist_en_passant[file]
        return h

    def white_to_move(self):
        return self.board[64] == 'w'

    def legal_moves(self):
        if self.board is None:
            raise ValueError("Engine not initialized. Call new() or load() before using this method.")
        turn = self.board[64]
        legal_moves = []
        starting_coordinates = [
            i for i, piece in enumerate(self.board[:64])
            if (turn == 'w' and piece.isupper()) or (turn == 'b' and piece.islower())
        ]
        opponent_moves = self.dangerous_squares(self.board)
        en_passant_target = self.board[69]
        for start in starting_coordinates:
            piece = self.board[start]
            if piece.upper() == 'P':
                direction = -1 if piece.isupper() else 1
                forward_one = start + (direction * 8)
                if 0 <= forward_one < 64 and self.board[forward_one] == ' ':
                    if (piece.isupper() and forward_one < 8) or (piece.islower() and forward_one >= 56):
                        for promo_piece in ['Q', 'R', 'B', 'N']:
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(forward_one)}{promo_piece.lower()}')
                    else:
                        legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(forward_one)}')

                    if (piece.isupper() and start // 8 == 6) or (piece.islower() and start // 8 == 1):
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
                                    legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}{promo_piece.lower()}')
                            else:
                                legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
                        elif target == en_passant_target:
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
                        if target_piece == ' ':
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
                        elif (target_piece.islower() if piece.isupper() else target_piece.isupper()):
                            legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
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
                            if target not in opponent_moves:
                                legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(target)}')
                rights = self.castling_rights(self.board, start, opponent_moves)
                if rights['king_side']:
                    legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(start + 2)}')
                if rights['queen_side']:
                    legal_moves.append(f'{self.index_to_square(start)}{self.index_to_square(start - 2)}')
        safe_moves = []
        for move in legal_moves:
            temp_board = self.board.copy()
            temp_hash = self.position_hash
            self.move(move, test=True, temp_board=temp_board)
            if not self.check(temp_board, turn):
                safe_moves.append(move)
            self.position_hash = temp_hash
        return safe_moves

    def check(self, board, turn):
        king_pos = board.index('K' if turn == 'w' else 'k')
        opponent_moves = self.dangerous_squares(board)
        return king_pos in opponent_moves

    def castling_rights(self, board, king_pos, opponent_moves):
        rights = {'king_side': False, 'queen_side': False}
        if board[64] == 'w':
            if board[65]:
                if board[63] == 'R':
                    if board[61] == ' ' and board[62] == ' ':
                        if king_pos not in opponent_moves and (king_pos + 1) not in opponent_moves and (king_pos + 2) not in opponent_moves:
                            rights['king_side'] = True
            if board[66]:
                if board[56] == 'R':
                    if board[57] == ' ' and board[58] == ' ' and board[59] == ' ':
                        if king_pos not in opponent_moves and (king_pos - 1) not in opponent_moves and (king_pos - 2) not in opponent_moves:
                            rights['queen_side'] = True
        else:
            if board[67]:
                if board[7] == 'r':
                    if board[5] == ' ' and board[6] == ' ':
                        if king_pos not in opponent_moves and (king_pos + 1) not in opponent_moves and (king_pos + 2) not in opponent_moves:
                            rights['king_side'] = True
            if board[68]:
                if board[0] == 'r':
                    if board[1] == ' ' and board[2] == ' ' and board[3] == ' ':
                        if king_pos not in opponent_moves and (king_pos - 1) not in opponent_moves and (king_pos - 2) not in opponent_moves:
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
                board[65] = False  
                board[66] = False  
            else:
                board[67] = False  
                board[68] = False  
            if not test:
                self.position_hash ^= self.zobrist_piece[moving_piece][start_index]
                self.position_hash ^= self.zobrist_piece[rook_piece][rook_start]
                self.position_hash ^= self.zobrist_piece[moving_piece][end_index]
                self.position_hash ^= self.zobrist_piece[rook_piece][rook_end]
                if moving_piece.isupper():
                    if board[65]:
                        self.position_hash ^= self.zobrist_castling['K']
                        board[65] = False
                    if board[66]:
                        self.position_hash ^= self.zobrist_castling['Q']
                        board[66] = False
                else:
                    if board[67]:
                        self.position_hash ^= self.zobrist_castling['k']
                        board[67] = False
                    if board[68]:
                        self.position_hash ^= self.zobrist_castling['q']
                        board[68] = False
        else:
            en_passant_target = board[69]
            if moving_piece.upper() == 'P' and end_index == en_passant_target:
                if moving_piece.isupper():
                    capture_index = end_index + 8
                else:
                    capture_index = end_index - 8
                captured_pawn = board[capture_index]
                board[capture_index] = ' '
                if not test:
                    self.position_hash ^= self.zobrist_piece[captured_pawn][capture_index]
            board[start_index] = ' '
            if promotion_piece:
                if moving_piece.isupper():
                    promoted_piece = promotion_piece.upper()
                else:
                    promoted_piece = promotion_piece.lower()
                board[end_index] = promoted_piece
            else:
                board[end_index] = moving_piece
            if moving_piece.upper() == 'R':
                if moving_piece.isupper():
                    if start_index == 56:
                        if board[66]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['Q']
                            board[66] = False
                    elif start_index == 63:

                        if board[65]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['K']
                            board[65] = False
                else:
                    if start_index == 0:
                        if board[68]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['q']
                            board[68] = False
                    elif start_index == 7:
                        if board[67]:
                            if not test:
                                self.position_hash ^= self.zobrist_castling['k']
                            board[67] = False
            if moving_piece.upper() == 'P' and abs(start_index - end_index) == 16:
                if not test and board[69] != -1:
                    file = board[69] % 8
                    self.position_hash ^= self.zobrist_en_passant[file]
                if moving_piece.isupper():
                    board[69] = start_index - 8
                else:
                    board[69] = start_index + 8
                if not test:
                    file = board[69] % 8
                    self.position_hash ^= self.zobrist_en_passant[file]
            else:
                if not test and board[69] != -1:
                    file = board[69] % 8
                    self.position_hash ^= self.zobrist_en_passant[file]
                board[69] = -1
            if not test:
                self.position_hash ^= self.zobrist_piece[moving_piece][start_index]
                if target_piece != ' ':
                    self.position_hash ^= self.zobrist_piece[target_piece][end_index]
                self.position_hash ^= self.zobrist_piece[board[end_index]][end_index]
                if moving_piece.upper() == 'K':
                    if moving_piece.isupper():
                        if board[65]:
                            self.position_hash ^= self.zobrist_castling['K']
                            board[65] = False
                        if board[66]:
                            self.position_hash ^= self.zobrist_castling['Q']
                            board[66] = False
                    else:
                        if board[67]:
                            self.position_hash ^= self.zobrist_castling['k']
                            board[67] = False
                        if board[68]:
                            self.position_hash ^= self.zobrist_castling['q']
                            board[68] = False
        if not test:
            if moving_piece.upper() == 'P' or target_piece != ' ' or promotion_piece:
                board[70] = 0  
            else:
                board[70] += 1  
        if not test:
            board[64] = 'b' if board[64] == 'w' else 'w'
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
        rank = 8 - index // 8
        return f'{chr(file + ord("a"))}{rank}'

    def dangerous_squares(self, board):
        opponent_moves = set()
        opponent_turn = 'b' if self.white_to_move() else 'w'
        starting_coordinates = [
            i for i, piece in enumerate(board[:64])
            if (opponent_turn == 'w' and piece.isupper()) or (opponent_turn == 'b' and piece.islower())
        ]
        for start in starting_coordinates:
            piece = board[start]
            if piece.upper() == 'P':
                direction = -1 if piece.isupper() else 1
                for dx in [-1, 1]:
                    x = (start % 8) + dx
                    y = (start // 8) + direction
                    if 0 <= x < 8 and 0 <= y < 8:
                        target = y * 8 + x
                        opponent_moves.add(target)
            elif piece.upper() == 'N':
                knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
                x = start % 8
                y = start // 8
                for dx, dy in knight_moves:
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        opponent_moves.add(target)
            elif piece.upper() in ['B', 'R', 'Q']:
                directions = []
                if piece.upper() == 'B':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                elif piece.upper() == 'R':
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                elif piece.upper() == 'Q':
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
                x = start % 8
                y = start // 8
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    while 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        opponent_moves.add(target)
                        if board[target] != ' ':
                            break
                        nx += dx
                        ny += dy
            elif piece.upper() == 'K':
                x = start % 8
                y = start // 8
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target = ny * 8 + nx
                        opponent_moves.add(target)
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
        return self.board[70] >= 100

    def stalemate(self):
        if not self.legal_moves():
            return not self.check(self.board, self.board[64])
        return False

    def three_fold_repetition(self):
        return self.position_hash_counts.get(self.position_hash, 0) >= 3

    def checkmate(self):
        if self.check(self.board, self.board[64]):
            return not self.legal_moves()
        return False