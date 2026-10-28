import math
import tkinter as tk

from board import Board
from game import Game
from move import Move


class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.resizable(False, False)

        self.game = Game()
        self.preview_board = Board()
        self.preview_mode = True
        self.selected_peg = None

        self.size_var = tk.StringVar(value="7")
        self.type_var = tk.StringVar(value="English")
        self.hints_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Choose a board and click New Game.")
        self.count_var = tk.StringVar()

        # One simple bordered area, like the instruction's example
        window = tk.Frame(root, bg="white", bd=1, relief="solid")
        window.pack(padx=10, pady=10)

        # Board selection on the left
        left = tk.Frame(window, bg="white")
        left.grid(row=0, column=0, sticky="nw", padx=(10, 2), pady=(72, 0))
        tk.Label(left, text="Board Type", bg="white").pack(anchor="w")

        for board_type in ("English", "Hexagon", "Diamond"):
            tk.Radiobutton(
                left, text=board_type, variable=self.type_var,
                value=board_type, command=self.show_preview,
                bg="white", activebackground="white"
            ).pack(anchor="w")

        tk.Checkbutton(
            left, text="Show valid moves", variable=self.hints_var,
            command=self.draw_board, bg="white", activebackground="white"
        ).pack(anchor="w", pady=(16, 0))

        # Board drawn in the middle
        self.canvas = tk.Canvas(
            window, width=350, height=330, bg="white",
            borderwidth=0, highlightthickness=0
        )
        self.canvas.grid(row=0, column=1, padx=4, pady=10)

        # Size and game buttons on the right
        right = tk.Frame(window, bg="white")
        right.grid(row=0, column=2, sticky="n", padx=(2, 12), pady=(14, 0))
        tk.Label(right, text="Board size", bg="white").pack()
        size_menu = tk.OptionMenu(
            right, self.size_var, "5", "7", "9", "11",
            command=self.show_preview
        )
        size_menu.config(width=4)
        size_menu.pack(pady=(4, 28))

        tk.Button(right, text="New Game", command=self.new_game).pack(fill="x")
        self.undo_button = tk.Button(right, text="Undo", command=self.undo_move)
        self.undo_button.pack(fill="x", pady=(8, 0))

        # Basic text at the bottom
        tk.Label(window, textvariable=self.status_var, bg="white").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 2)
        )
        tk.Label(window, textvariable=self.count_var, bg="white").grid(
            row=2, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 10)
        )

        self.draw_board()

    def show_preview(self, *args):
        self.preview_board = Board(int(self.size_var.get()), self.type_var.get())
        self.preview_mode = True
        self.selected_peg = None
        self.status_var.set("Board preview. Click New Game to play.")
        self.draw_board()

    def new_game(self):
        self.game.start_new_game(int(self.size_var.get()), self.type_var.get())
        self.preview_mode = False
        self.selected_peg = None
        self.status_var.set("Select a peg, then an empty hole.")
        self.draw_board()

    def undo_move(self):
        if self.game.undo_move():
            self.selected_peg = None
            self.status_var.set("Last move undone.")
            self.draw_board()
        else:
            self.status_var.set("Nothing to undo.")

    def draw_board(self):
        self.canvas.delete("all")
        board = self.preview_board if self.preview_mode else self.game.board
        center = board.size // 2
        spacing = min(38, 300 / board.size)
        center_x, center_y = 175, 165

        hints = set()
        if self.hints_var.get() and not self.preview_mode and self.selected_peg is not None:
            for move in self.game.get_valid_moves():
                if (move.start_row, move.start_col) == self.selected_peg:
                    hints.add((move.end_row, move.end_col))

        for row in range(board.size):
            for col in range(board.size):
                cell = board.get_cell(row, col)
                if cell == Board.INVALID:
                    continue

                selected = (row, col) == self.selected_peg
                fill = "#cccccc" if selected else ("#eeeeee" if (row, col) in hints else "white")
                tags = ("cell", f"{row}:{col}")

                if board.board_type == "Hexagon":
                    # A skewed stored grid, displayed as a regular hexagon
                    x = center_x + (col - row / 2 - center / 2) * spacing
                    y = center_y + (row - center) * spacing * math.sqrt(3) / 2
                    radius = spacing / math.sqrt(3)
                    points = []
                    for i in range(6):
                        angle = math.radians(60 * i - 90)
                        points.extend((
                            x + radius * math.cos(angle),
                            y + radius * math.sin(angle)
                        ))
                    self.canvas.create_polygon(points, fill=fill, outline="black", tags=tags)
                else:
                    x = center_x + (col - center) * spacing
                    y = center_y + (row - center) * spacing
                    half = spacing / 2
                    self.canvas.create_rectangle(
                        x - half, y - half, x + half, y + half,
                        fill=fill, outline="black", tags=tags
                    )

                peg_radius = spacing * 0.30
                color = "black" if cell == Board.PEG else "white"
                self.canvas.create_oval(
                    x - peg_radius, y - peg_radius,
                    x + peg_radius, y + peg_radius,
                    fill=color, outline="black", tags=tags
                )

        self.canvas.tag_bind("cell", "<Button-1>", self.on_cell_click)
        self.count_var.set(f"Pegs remaining: {sum(r.count(Board.PEG) for r in board.get_grid())}")
        self.undo_button.config(state="disabled" if self.preview_mode else "normal")

    def on_cell_click(self, event):
        if self.preview_mode:
            self.status_var.set("Click New Game before playing.")
            return
        if self.game.is_game_over():
            self.show_result()
            return

        tags = self.canvas.gettags("current")
        position = next((t for t in tags if ":" in t), None)
        if position is None:
            return
        row, col = map(int, position.split(":"))

        if self.game.board.get_cell(row, col) == Board.PEG:
            self.selected_peg = None if self.selected_peg == (row, col) else (row, col)
            self.status_var.set("Click an empty hole." if self.selected_peg else "Selection cleared.")
        elif self.selected_peg is None:
            self.status_var.set("Select a peg first.")
        else:
            move = Move(*self.selected_peg, row, col)
            if self.game.make_move(move):
                self.selected_peg = None
                if self.game.is_game_over():
                    self.show_result()
                else:
                    self.status_var.set("Move made.")
            else:
                self.status_var.set("Invalid move.")

        self.draw_board()

    def show_result(self):
        self.status_var.set(f"Game over! Rating: {self.game.get_rating()}.")
