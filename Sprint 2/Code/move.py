from dataclasses import dataclass

# frozen = True so Move is immutable (can't be changed after creation)
# helpful for implementing undo / redo, so move history can't change
@dataclass(frozen=True)
class Move:
    start_row: int
    start_col: int
    end_row: int
    end_col: int
