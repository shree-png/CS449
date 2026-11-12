### Read and write the JSON format used for game replay

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from board import Board


def save_recording(path, *, board_size, board_type, mode, states):
    data = {
        "board_size": board_size,
        "board_type": board_type,
        "mode": mode,
        "states": states,
    }
    path = Path(path)
    output = NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    )
    temporary_path = Path(output.name)
    try:
        with output:
            json.dump(data, output)
            output.write("\n")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def load_recording(path, *, valid_modes):
    with open(path, encoding="utf-8") as source:
        data = json.load(source)

    if not isinstance(data, dict):
        raise ValueError("The recording must contain a game object.")

    mode = data.get("mode")
    if mode not in valid_modes:
        raise ValueError("The recording has an unknown game mode.")

    states = data.get("states")
    if not isinstance(states, list) or not states:
        raise ValueError("The recording contains no board states.")

    boards = []
    for grid in states:
        board = Board(data.get("board_size"), data.get("board_type"))
        if not isinstance(grid, list) or len(grid) != board.size:
            raise ValueError("A recorded board does not match its size.")

        for row, cells in enumerate(grid):
            if not isinstance(cells, list) or len(cells) != board.size:
                raise ValueError("A recorded board row does not match its size.")
            for col, state in enumerate(cells):
                playable = board.is_valid_position(row, col)
                allowed = (Board.EMPTY, Board.PEG) if playable else (Board.INVALID,)
                if type(state) is not int or state not in allowed:
                    raise ValueError("A recorded cell does not match the board layout.")
                if playable:
                    board.set_cell(row, col, state)

        boards.append(board)

    return mode, boards
