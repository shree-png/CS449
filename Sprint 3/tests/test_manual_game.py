import unittest
from board import Board
from move import Move
from game import Game


class TestGame(unittest.TestCase):

    def test_default_game(self):
        game = Game()

        self.assertEqual(game.board.size, 7)
        self.assertEqual(game.board.board_type, "English")

    def test_ac_3_1_start_new_game(self):
        game = Game()

        game.make_move(Move(3, 1, 3, 3))
        game.start_new_game(5, "Diamond")

        self.assertEqual(game.board.size, 5)
        self.assertEqual(game.board.board_type, "Diamond")
        self.assertEqual(
            game.board.get_grid(),
            Board(5, "Diamond").get_grid()
        )

        # Previous move history should be cleared
        self.assertFalse(game.undo_move())

    def test_ac_4_1_valid_orthogonal_move(self):
        for board_type in ("English", "Diamond", "Hexagon"):
            with self.subTest(board_type=board_type):
                game = Game(board_type=board_type)

                self.assertTrue(
                    game.make_move(Move(3, 1, 3, 3))
                )

                self.assertEqual(
                    game.board.get_cell(3, 1), Board.EMPTY
                )
                self.assertEqual(
                    game.board.get_cell(3, 2), Board.EMPTY
                )
                self.assertEqual(
                    game.board.get_cell(3, 3), Board.PEG
                )

    def test_ac_4_1_hexagon_diagonal_move(self):
        game = Game(board_type="Hexagon")

        self.assertTrue(
            game.make_move(Move(1, 1, 3, 3))
        )

        self.assertEqual(
            game.board.get_cell(1, 1), Board.EMPTY
        )
        self.assertEqual(
            game.board.get_cell(2, 2), Board.EMPTY
        )
        self.assertEqual(
            game.board.get_cell(3, 3), Board.PEG
        )

    def test_ac_4_2_invalid_move(self):
        game = Game()
        original = game.board.get_grid()

        self.assertFalse(
            game.make_move(Move(3, 1, 3, 2))
        )

        self.assertEqual(game.board.get_grid(), original)

    def test_diagonal_not_allowed_on_diamond(self):
        game = Game(board_type="Diamond")

        game.board.set_cell(3, 3, Board.PEG)
        game.board.set_cell(4, 4, Board.EMPTY)

        original = game.board.get_grid()

        self.assertFalse(
            game.make_move(Move(2, 2, 4, 4))
        )
        self.assertEqual(game.board.get_grid(), original)

    def test_ac_4_3_undo_move(self):
        game = Game()
        original = game.board.get_grid()

        game.make_move(Move(3, 1, 3, 3))

        self.assertTrue(game.undo_move())
        self.assertEqual(game.board.get_grid(), original)

    def test_undo_with_no_history(self):
        game = Game()
        original = game.board.get_grid()

        self.assertFalse(game.undo_move())
        self.assertEqual(game.board.get_grid(), original)

    def test_game_not_over_initially(self):
        game = Game()

        self.assertFalse(game.is_game_over())

    def test_game_over_with_one_peg(self):
        game = Game()

        for row in range(game.board.size):
            for col in range(game.board.size):
                if game.board.is_valid_position(row, col):
                    game.board.set_cell(row, col, Board.EMPTY)

        game.board.set_cell(3, 3, Board.PEG)

        self.assertTrue(game.is_game_over())

    def test_get_peg_count(self):
        game = Game()

        # Default English board has 32 pegs
        self.assertEqual(game.get_peg_count(), 32)

        game.make_move(Move(3, 1, 3, 3))

        # Each valid jump removes 1 peg
        self.assertEqual(game.get_peg_count(), 31)

    def create_finished_game(self, peg_count):
        game = Game(5, "Diamond")

        # Empty every playable position
        for row in range(game.board.size):
            for col in range(game.board.size):
                if game.board.is_valid_position(row, col):
                    game.board.set_cell(row, col, Board.EMPTY)

        # Use isolated positions that cannot jump
        positions = [(0, 2), (2, 0), (2, 4), (4, 2)]

        for row, col in positions[:peg_count]:
            game.board.set_cell(row, col, Board.PEG)

        return game

    def test_ac_5_1_outstanding_rating(self):
        game = self.create_finished_game(1)

        self.assertTrue(game.is_game_over())
        self.assertEqual(game.get_rating(), "Outstanding")

    def test_ac_5_2_remaining_peg_ratings(self):
        ratings = {
            2: "Very Good",
            3: "Good",
            4: "Average"
        }

        for peg_count, expected_rating in ratings.items():
            with self.subTest(pegs=peg_count):
                game = self.create_finished_game(peg_count)

                self.assertTrue(game.is_game_over())
                self.assertEqual(game.get_rating(), expected_rating)

    def test_no_rating_while_playing(self):
        game = Game()

        self.assertFalse(game.is_game_over())
        self.assertIsNone(game.get_rating())
