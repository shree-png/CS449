import random

import recording
from board import Board
from move import Move


class BaseGame:
    ### Board state and move rules shared by both game modes

    MODE: str

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
        self._recorded_states = [self.board.get_grid()]

    def start_new_game(self, size=7, board_type="English"):
        self.board = Board(size, board_type)
        self._recorded_states = [self.board.get_grid()]

    def _record_board(self):
        self._recorded_states.append(self.board.get_grid())

    def save_recording(self, path):
        ###Write this game's board states, in order, to a text file
        recording.save_recording(
            path,
            board_size=self.board.size,
            board_type=self.board.board_type,
            mode=self.MODE,
            states=self._recorded_states,
        )

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

        self._record_board()
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
        return self.board.peg_count()

    def is_game_over(self):
        return (
            self.get_peg_count() == 1
            or not self.get_valid_moves()
        )


class ManualGame(BaseGame):
    ###Player-controlled game with undo history and an end rating

    MODE = "Manual"

    def __init__(self, size=7, board_type="English"):
        super().__init__(size, board_type)
        self._move_history = []

    def start_new_game(self, size=7, board_type="English"):
        super().start_new_game(size, board_type)
        self._move_history.clear()

    def make_move(self, move):
        previous_grid = self.board.get_grid()
        if not super().make_move(move):
            return False

        self._move_history.append(previous_grid)
        return True

    def undo_move(self):
        if not self._move_history:
            return False

        previous_grid = self._move_history.pop()
        for row, cells in enumerate(previous_grid):
            for col, state in enumerate(cells):
                if state != Board.INVALID:
                    self.board.set_cell(row, col, state)
        self._record_board()
        return True

    def randomize_board(self):
        ### Rearrange the remaining pegs on the current board
        if self.is_game_over():
            return False

        previous_grid = self.board.get_grid()
        positions = []
        current_pegs = set()
        for row, cells in enumerate(previous_grid):
            for col, state in enumerate(cells):
                if state != Board.INVALID:
                    positions.append((row, col))
                if state == Board.PEG:
                    current_pegs.add((row, col))

        new_pegs = current_pegs
        while new_pegs == current_pegs:
            new_pegs = set(random.sample(positions, len(current_pegs)))

        for row, col in positions:
            state = Board.PEG if (row, col) in new_pegs else Board.EMPTY
            self.board.set_cell(row, col, state)

        self._move_history.append(previous_grid)
        self._record_board()
        return True

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


class AutomatedGame(BaseGame):
    ###Computer-controlled game that makes one random legal move per turn

    MODE = "Automated"

    def play_turn(self):
        valid_moves = self.get_valid_moves()
        if not valid_moves:
            return False

        return self.make_move(random.choice(valid_moves))


def load_recording(path):
    ### Read a saved game and reconstruct its boards in playback order
    return recording.load_recording(
        path, valid_modes=(ManualGame.MODE, AutomatedGame.MODE)
    )


# Preserve the original manual game API for existing callers and tests
Game = ManualGame
