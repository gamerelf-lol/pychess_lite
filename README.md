# PyChess Lite

### Examples

```py
from pychess_lite import Engine

game = Engine.new() # Creates a new game.

game.board # A 1-D array whose elements correspond to the squares on the 8x8 chess board ordered from top-to-bottom, left-to-right.
game.legal_moves() # Returns a list of legal moves.

move = 'e2e4'
game.move(move) # Changes the state of the board given a legal move.

game.white_to_move() # Returns True if the player to move is white.

game.check() # Returns True if the player to move is in check.

game.castling_rights() # Returns a dictionary containing boolean "king_side" and "queen_side" key value pairs, given the player to move's castling privileges.

game.dangerous_squares() # Returns a set of integers representing the board indices that the player to move's opponent could potentially attack or occupy on their next move.

game.insufficient_material() # Returns True if both White and Black do not have sufficient material to force a checkmate.

game.fifty_move_rule() # Returns True if more than 50 turns have passed since the last capture or pawn move.

game.three_fold_repetition() # Returns True if the same board position has was repeated three times in a game.

game.stalemate() # Returns True if the player to move has no legal moves but is not in check.

game.checkmate() # Returns True if the player to mvoe has no legal moves and is in check.
```

This project is licensed under the [DWETFYWWI](https://opensource.org/license/Do_whatever_the_fuck_you_want_with_it) License.
