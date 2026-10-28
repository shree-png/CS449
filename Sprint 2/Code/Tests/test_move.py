import unittest
from dataclasses import FrozenInstanceError
from move import Move

class TestMove(unittest.TestCase):
    def test_move_coordinates(self):
        move = Move(3, 1, 3, 3)

        self.assertEqual(move.start_row, 3)
        self.assertEqual(move.start_col, 1)
        self.assertEqual(move.end_row, 3)
        self.assertEqual(move.end_col, 3)

    def test_move_equality(self):
        move1 = Move(3, 1, 3, 3)
        move2 = Move(3, 1, 3, 3)

        self.assertEqual(move1, move2)

    def test_move_immutable(self):
        move = Move(3, 1, 3, 3)

        with self.assertRaises(FrozenInstanceError):
            move.start_row = 2
