from board import Board
from move import Move


class Game:
    ORTHOGONAL_DIRECTIONS = [
        (-1, 0), (1, 0),
        (0, -1), (0, 1)
    ]

    HEX_DIRECTIONS = [
        (-1, 0), (1, 0),
        (0, -1), (0, 1),
        (-1, -1), (1, 1)
    ]

    def __init__(self, size=7, board_type="English"):
        self.board = Board(size, board_type)
        self._move_history = []

    def start_new_game(self, size=7, board_type="English"):
        self.board = Board(size, board_type)
        self._move_history.clear()

    def _get_directions(self):
        if self.board.board_type == "Hexagon":
            return self.HEX_DIRECTIONS
        return self.ORTHOGONAL_DIRECTIONS

    def is_valid_move(self, move):
        if not isinstance(move, Move):
            return False

        if any(type(value) is not int for value in (
            move.start_row, move.start_col,
            move.end_row, move.end_col
        )):
            return False

        row_change = move.end_row - move.start_row
        col_change = move.end_col - move.start_col

        # A jump must travel exactly two steps
        if (row_change, col_change) not in [
            (2 * dr, 2 * dc)
            for dr, dc in self._get_directions()
        ]:
            return False

        middle_row = (move.start_row + move.end_row) // 2
        middle_col = (move.start_col + move.end_col) // 2

        positions = [
            (move.start_row, move.start_col),
            (middle_row, middle_col),
            (move.end_row, move.end_col)
        ]

        # All three positions must be playable
        if not all(
            self.board.is_valid_position(r, c)
            for r, c in positions
        ):
            return False

        # Start and middle must have pegs;
        # destination must be empty
        return (
            self.board.get_cell(
                move.start_row, move.start_col
            ) == Board.PEG
            and self.board.get_cell(
                middle_row, middle_col
            ) == Board.PEG
            and self.board.get_cell(
                move.end_row, move.end_col
            ) == Board.EMPTY
        )

    def make_move(self, move):
        if not self.is_valid_move(move):
            return False

        middle_row = (move.start_row + move.end_row) // 2
        middle_col = (move.start_col + move.end_col) // 2

        self.board.set_cell(
            move.start_row, move.start_col, Board.EMPTY
        )
        self.board.set_cell(
            middle_row, middle_col, Board.EMPTY
        )
        self.board.set_cell(
            move.end_row, move.end_col, Board.PEG
        )

        self._move_history.append(move)
        return True

    def undo_move(self):
        if not self._move_history:
            return False

        move = self._move_history.pop()

        middle_row = (move.start_row + move.end_row) // 2
        middle_col = (move.start_col + move.end_col) // 2

        self.board.set_cell(
            move.start_row, move.start_col, Board.PEG
        )
        self.board.set_cell(
            middle_row, middle_col, Board.PEG
        )
        self.board.set_cell(
            move.end_row, move.end_col, Board.EMPTY
        )

        return True

    def get_valid_moves(self):
        valid_moves = []

        for row in range(self.board.size):
            for col in range(self.board.size):
                if not self.board.is_valid_position(row, col):
                    continue

                if self.board.get_cell(row, col) != Board.PEG:
                    continue

                for dr, dc in self._get_directions():
                    move = Move(
                        row, col,
                        row + 2 * dr,
                        col + 2 * dc
                    )

                    if self.is_valid_move(move):
                        valid_moves.append(move)

        return valid_moves

    def get_peg_count(self):
        return sum(
            row.count(Board.PEG)
            for row in self.board.get_grid()
        )

    def is_game_over(self):
        return (
            self.get_peg_count() == 1
            or len(self.get_valid_moves()) == 0
        )

    def get_rating(self):
        if not self.is_game_over():
            return None

        pegs = self.get_peg_count()

        if pegs == 1:
            return "Outstanding"
        elif pegs == 2:
            return "Very Good"
        elif pegs == 3:
            return "Good"
        else:
            return "Average"
