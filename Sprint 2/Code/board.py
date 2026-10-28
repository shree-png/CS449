class Board:
    INVALID = -1
    EMPTY = 0
    PEG = 1

    def __init__(self, size=7, board_type="English"):
        if type(size) is not int or not (5 <= size <= 11) or size % 2 == 0:
            raise ValueError("Board size must be an odd integer between 5 and 11.")

        if board_type not in ("English", "Hexagon", "Diamond"):
            raise ValueError("Invalid board type.")

        self._size = size
        self._board_type = board_type
        self._grid = []

        self.initialize_board()

    @property
    def size(self):
        return self._size

    @property
    def board_type(self):
        return self._board_type

    def initialize_board(self):
        # Create the board with the center hole empty
        self._grid = [
            [self.INVALID for _ in range(self._size)]
            for _ in range(self._size)
        ]

        for row in range(self._size):
            for col in range(self._size):
                if self._is_playable_shape_cell(row, col):
                    self._grid[row][col] = self.PEG

        center = self._size // 2
        self._grid[center][center] = self.EMPTY

    def _is_playable_shape_cell(self, row, col):
        # Determine whether a cell belongs to the board shape
        center = self._size // 2

        if self._board_type == "English":
            return (
                abs(row - center) <= 1
                or abs(col - center) <= 1
            )

        elif self._board_type == "Diamond":
            return (
                abs(row - center) + abs(col - center)
                <= center
            )

        elif self._board_type == "Hexagon":
            return max(
                abs(row - center),
                abs(col - center),
                abs(row - col)
            ) <= center

    def is_valid_position(self, row, col):
       # Check whether a position is playable
        return (
            0 <= row < self._size
            and 0 <= col < self._size
            and self._grid[row][col] != self.INVALID
        )

    def get_cell(self, row, col):
        # Return the state of a cell
        if not (0 <= row < self._size and 0 <= col < self._size):
            raise IndexError("Position is outside the grid.")

        return self._grid[row][col]

    def set_cell(self, row, col, state):
        # Update the state of a playable cell
        if state not in (self.EMPTY, self.PEG):
            raise ValueError("Cell state must be EMPTY or PEG.")

        if not self.is_valid_position(row, col):
            raise ValueError("Position is not playable.")

        self._grid[row][col] = state

    def get_grid(self):
        # Return a copy of the board grid
        return [row.copy() for row in self._grid]
