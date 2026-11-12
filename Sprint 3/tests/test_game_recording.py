import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from board import Board
from game import AutomatedGame, ManualGame, load_recording
from move import Move


class TestGameRecording(unittest.TestCase):
    def read_recording(self, game):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "game.txt"
            game.save_recording(path)
            return json.loads(path.read_text(encoding="utf-8"))

    def test_manual_recording_includes_move_and_undo_once(self):
        game = ManualGame()
        start = game.board.get_grid()
        self.assertFalse(game.make_move(Move(3, 1, 3, 2)))
        self.assertTrue(game.make_move(game.get_valid_moves()[0]))
        after_move = game.board.get_grid()
        self.assertTrue(game.undo_move())
        self.assertFalse(game.undo_move())

        self.assertEqual(self.read_recording(game), {
            "board_size": 7,
            "board_type": "English",
            "mode": "Manual",
            "states": [start, after_move, start],
        })

    def test_automated_recording_contains_the_chosen_move(self):
        game = AutomatedGame(size=9, board_type="Hexagon")
        start = game.board.get_grid()
        move = game.get_valid_moves()[-1]

        with patch("game.random.choice", return_value=move):
            self.assertTrue(game.play_turn())

        self.assertEqual(game.board.get_cell(move.end_row, move.end_col), Board.PEG)
        self.assertEqual(self.read_recording(game), {
            "board_size": 9,
            "board_type": "Hexagon",
            "mode": "Automated",
            "states": [start, game.board.get_grid()],
        })

    def test_randomization_and_undo_appear_in_order(self):
        game = ManualGame()
        start = game.board.get_grid()
        peg_positions = [
            (row, col)
            for row, cells in enumerate(start)
            for col, state in enumerate(cells)
            if state != Board.INVALID and (row, col) != (3, 2)
        ]
        count = game.get_peg_count()

        with patch("game.random.sample", return_value=peg_positions):
            self.assertTrue(game.randomize_board())

        randomized = game.board.get_grid()
        self.assertNotEqual(randomized, start)
        self.assertEqual(game.get_peg_count(), count)
        self.assertTrue(game.make_move(game.get_valid_moves()[0]))
        after_move = game.board.get_grid()
        self.assertTrue(game.undo_move())
        self.assertTrue(game.undo_move())
        self.assertFalse(game.undo_move())
        self.assertEqual(self.read_recording(game)["states"], [
            start, randomized, after_move, randomized, start,
        ])

    def test_new_game_resets_the_recording_and_undo(self):
        game = ManualGame()
        self.assertTrue(game.make_move(game.get_valid_moves()[0]))
        game.start_new_game(5, "Diamond")

        self.assertFalse(game.undo_move())
        self.assertEqual(self.read_recording(game), {
            "board_size": 5,
            "board_type": "Diamond",
            "mode": "Manual",
            "states": [game.board.get_grid()],
        })

    def test_replay_loads_manual_jumps_undos_and_shuffles_in_order(self):
        game = ManualGame(size=5, board_type="Diamond")
        start = game.board.get_grid()
        self.assertTrue(game.make_move(game.get_valid_moves()[0]))
        after_jump = game.board.get_grid()
        self.assertTrue(game.undo_move())
        self.assertTrue(game.randomize_board())
        after_shuffle = game.board.get_grid()

        with TemporaryDirectory() as directory:
            path = Path(directory) / "recording.txt"
            game.save_recording(path)
            mode, boards = load_recording(path)

        self.assertEqual(mode, "Manual")
        self.assertTrue(all(board.board_type == "Diamond" for board in boards))
        self.assertEqual([board.get_grid() for board in boards], [
            start, after_jump, start, after_shuffle,
        ])

    def test_replay_loads_automated_board_type_and_frames(self):
        game = AutomatedGame(size=9, board_type="Hexagon")
        start = game.board.get_grid()
        self.assertTrue(game.play_turn())

        with TemporaryDirectory() as directory:
            path = Path(directory) / "recording.txt"
            game.save_recording(path)
            mode, boards = load_recording(path)

        self.assertEqual(mode, "Automated")
        self.assertEqual([(board.size, board.board_type) for board in boards], [
            (9, "Hexagon"), (9, "Hexagon"),
        ])
        self.assertEqual([board.get_grid() for board in boards], [start, game.board.get_grid()])

    def test_replay_rejects_an_invalid_board_frame(self):
        game = ManualGame()
        self.assertTrue(game.make_move(game.get_valid_moves()[0]))
        recording = self.read_recording(game)
        recording["states"][1][0][0] = Board.PEG

        with TemporaryDirectory() as directory:
            path = Path(directory) / "recording.txt"
            path.write_text(json.dumps(recording), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match the board layout"):
                load_recording(path)

    def test_failed_save_preserves_the_existing_recording(self):
        def fail_during_write(recording, output):
            output.write('{"partial":')
            raise OSError("write failed")

        game = AutomatedGame()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "game.txt"
            game.save_recording(path)
            original = path.read_bytes()

            with patch("recording.json.dump", side_effect=fail_during_write):
                with self.assertRaises(OSError):
                    game.save_recording(path)

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(path.parent.iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
