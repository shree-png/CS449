import unittest
from board import Board


class TestBoard(unittest.TestCase):

    # Helper method
    def check_initial_board(self, board):
        """Check that every playable cell has a peg except the center."""
        center = board.size // 2

        for row in range(board.size):
            for col in range(board.size):
                if (row, col) == (center, center):
                    self.assertEqual(board.get_cell(row, col), Board.EMPTY)
                elif board.is_valid_position(row, col):
                    self.assertEqual(board.get_cell(row, col), Board.PEG)
                else:
                    self.assertEqual(board.get_cell(row, col), Board.INVALID)

    ### Acceptance Criteria Tests

    # AC 1.1: Customizing a board size
    def test_ac_1_1_custom_board_size(self):
        for size in (5, 7, 9, 11):
            with self.subTest(size=size):
                board = Board(size, "English")

                self.assertEqual(board.size, size)

                grid = board.get_grid()
                self.assertEqual(len(grid), size)

                for row in grid:
                    self.assertEqual(len(row), size)

                self.check_initial_board(board)

    # AC 1.2: Default board size
    def test_ac_1_2_default_board_size(self):
        board = Board()

        self.assertEqual(board.size, 7)
        self.check_initial_board(board)

    # AC 2.1: Customizing a board type
    def test_ac_2_1_custom_board_type(self):
        for board_type in ("English", "Diamond", "Hexagon"):
            with self.subTest(board_type=board_type):
                board = Board(7, board_type)

                self.assertEqual(board.board_type, board_type)
                self.check_initial_board(board)

    # AC 2.2: Default board type
    def test_ac_2_2_default_board_type(self):
        board = Board()

        self.assertEqual(board.board_type, "English")
        self.check_initial_board(board)


    ### Additional Board Unit Tests

    def test_invalid_sizes(self):
        invalid_sizes = (4, 6, 8, 10, 12, 7.5, "7", True)

        for size in invalid_sizes:
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    Board(size)

    def test_invalid_board_types(self):
        invalid_types = ("Circle", "english", "", None)

        for board_type in invalid_types:
            with self.subTest(board_type=board_type):
                with self.assertRaises(ValueError):
                    Board(7, board_type)

    def test_is_valid_position(self):
        board = Board()

        self.assertTrue(board.is_valid_position(3, 3))
        self.assertTrue(board.is_valid_position(0, 3))

        self.assertFalse(board.is_valid_position(0, 0))
        self.assertFalse(board.is_valid_position(-1, 3))
        self.assertFalse(board.is_valid_position(7, 3))

    def test_get_cell(self):
        board = Board()

        self.assertEqual(board.get_cell(3, 3), Board.EMPTY)
        self.assertEqual(board.get_cell(2, 3), Board.PEG)
        self.assertEqual(board.get_cell(0, 0), Board.INVALID)

    def test_get_cell_out_of_bounds(self):
        board = Board()

        with self.assertRaises(IndexError):
            board.get_cell(7, 3)

        with self.assertRaises(IndexError):
            board.get_cell(-1, 3)

    def test_set_cell(self):
        board = Board()

        board.set_cell(3, 3, Board.PEG)
        self.assertEqual(board.get_cell(3, 3), Board.PEG)

        board.set_cell(3, 3, Board.EMPTY)
        self.assertEqual(board.get_cell(3, 3), Board.EMPTY)

    def test_set_cell_invalid_position(self):
        board = Board()

        with self.assertRaises(ValueError):
            board.set_cell(0, 0, Board.PEG)

        with self.assertRaises(ValueError):
            board.set_cell(7, 3, Board.PEG)

    def test_set_cell_invalid_state(self):
        board = Board()

        with self.assertRaises(ValueError):
            board.set_cell(3, 3, 5)

        with self.assertRaises(ValueError):
            board.set_cell(3, 3, Board.INVALID)

    def test_initialize_board_resets_board(self):
        board = Board()

        board.set_cell(3, 3, Board.PEG)
        board.set_cell(2, 3, Board.EMPTY)

        board.initialize_board()

        self.check_initial_board(board)

    def test_get_grid_returns_copy(self):
        board = Board()

        grid = board.get_grid()
        grid[3][3] = Board.PEG

        self.assertEqual(board.get_cell(3, 3), Board.EMPTY)

    
    ### Board Shape Tests

    def check_board_shape(self, board, expected_rows):
        """Compare the entire board to an expected layout."""
        symbols = {
            "X": Board.INVALID,
            "P": Board.PEG,
            ".": Board.EMPTY
        }

        expected_grid = [
            [symbols[cell] for cell in row]
            for row in expected_rows
        ]

        self.assertEqual(board.get_grid(), expected_grid)

    def test_english_board_shape(self):
        board = Board(7, "English")

        expected = [
            "XXPPPXX",
            "XXPPPXX",
            "PPPPPPP",
            "PPP.PPP",
            "PPPPPPP",
            "XXPPPXX",
            "XXPPPXX"
        ]

        self.check_board_shape(board, expected)

    def test_diamond_board_shape(self):
        board = Board(7, "Diamond")

        expected = [
            "XXXPXXX",
            "XXPPPXX",
            "XPPPPPX",
            "PPP.PPP",
            "XPPPPPX",
            "XXPPPXX",
            "XXXPXXX"
        ]

        self.check_board_shape(board, expected)

    def test_hexagon_board_shape(self):
        board = Board(7, "Hexagon")

        # looks skewed when stored in a square array,
        # will look normal when we implement the GUI
        expected = [
            "PPPPXXX",
            "PPPPPXX",
            "PPPPPPX",
            "PPP.PPP",
            "XPPPPPP",
            "XXPPPPP",
            "XXXPPPP"
        ]

        self.check_board_shape(board, expected)


if __name__ == "__main__":
    unittest.main()
