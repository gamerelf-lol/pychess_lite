# PyChess Lite

A super lightweight module designed to create, alter, and verify chess board states.

### Examples

```py
from pychess_lite import Board

game = Board.new() # Creates a new game.

game.board # A 1-D array whose elements correspond to the squares on the 8x8 chess board ordered from top-to-bottom, left-to-right.
game.legal_moves() # Returns a list of legal moves.

move = 'e2e4'
game.move(move) # Changes the state of the board given a legal move.

game.player_to_move() # Returns 'w' or 'b' depending on the player to move.
game.white_to_move() # Returns True if the player to move is white.
game.black_to_move() # Returns True if the player to move is black.

game.check() # Returns True if the player to move is in check.

game.castling_rights() # Returns a dictionary containing boolean "king_side" and "queen_side" key value pairs, given the player to move's castling privileges.

game.dangerous_squares() # Returns a set of integers representing the board indices that the player to move's opponent could potentially attack or occupy on their next move.

game.insufficient_material() # Returns True if both White and Black do not have sufficient material to force a checkmate.

game.fifty_move_rule() # Returns True if more than 50 turns have passed since the last capture or pawn move.

game.three_fold_repetition() # Returns True if the same board position has was repeated three times in a game.

game.stalemate() # Returns True if the player to move has no legal moves but is not in check.

game.checkmate() # Returns True if the player to move has no legal moves and is in check.

def scholars_mate():
    game = Board.new()
    moves = ['e2e4', 'e7e5', 'f1c4', 'b8c6', 'd1h5', 'g8f6', 'h5f7']
    for move in moves:
        game.move(move)
    return game.checkmate()

if __name__ == "__main__":
    print(scholars_mate()) # True
```

TODO:

1. Compability with chess algebraic notation and PGN import and exports.
2. Rewrite dangerous_squares to align their output with other instance methods.
3. Rewrite the return value of castling_rights to be a tuple.
4. Massive performance overhaul and refactoring in the near distant future.

This project is licensed under the [DWTFYPWI](https://dwtfypwi.org/license/Do_whatever_the_fuck_you_please_with_it) Public License.
