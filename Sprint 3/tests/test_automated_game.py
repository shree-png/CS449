import unittest
from unittest.mock import patch

from board import Board
from game import AutomatedGame
from move import Move


class TestAutomatedGame(unittest.TestCase):
    def setUp(self):
        self.game = AutomatedGame()

    def set_pegs(self, positions):
        board = self.game.board
        for row in range(board.size):
            for col in range(board.size):
                if board.is_valid_position(row, col):
                    board.set_cell(row, col, Board.EMPTY)
        for row, col in positions:
            board.set_cell(row, col, Board.PEG)

    def test_turn_chooses_and_applies_a_legal_move(self):
        legal_moves = self.game.get_valid_moves()
        move = Move(3, 1, 3, 3)
        self.assertGreater(len(legal_moves), 1)
        self.assertIn(move, legal_moves)
        count_before = self.game.get_peg_count()

        with patch("game.random.choice", return_value=move) as choose:
            self.assertTrue(self.game.play_turn())

        choose.assert_called_once_with(legal_moves)
        self.assertEqual(self.game.board.get_cell(3, 1), Board.EMPTY)
        self.assertEqual(self.game.board.get_cell(3, 2), Board.EMPTY)
        self.assertEqual(self.game.board.get_cell(3, 3), Board.PEG)
        self.assertEqual(self.game.get_peg_count(), count_before - 1)

    def test_turn_ends_the_game_when_one_peg_remains(self):
        self.set_pegs([(0, 2), (0, 3)])
        self.assertEqual(self.game.get_valid_moves(), [Move(0, 2, 0, 4)])
        self.assertFalse(self.game.is_game_over())

        self.assertTrue(self.game.play_turn())

        self.assertEqual(self.game.get_peg_count(), 1)
        self.assertTrue(self.game.is_game_over())
        self.assertFalse(self.game.play_turn())

    def test_game_ends_with_multiple_pegs_and_no_legal_moves(self):
        self.set_pegs([(0, 2), (6, 4)])
        grid_before = self.game.board.get_grid()

        self.assertEqual(self.game.get_peg_count(), 2)
        self.assertTrue(self.game.is_game_over())
        self.assertFalse(self.game.play_turn())
        self.assertEqual(self.game.board.get_grid(), grid_before)


if __name__ == "__main__":
    unittest.main()
