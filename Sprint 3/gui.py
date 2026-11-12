import math
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from board import Board
from game import AutomatedGame, ManualGame, load_recording
from move import Move


class GUI:
    AUTOMATED_TURN_DELAY_MS = 400
    REPLAY_FRAME_DELAY_MS = 400
    RECORDING_PATH = Path(__file__).resolve().with_name("recording.txt")

    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.resizable(False, False)

        self.game = ManualGame()
        self.preview_board = Board()
        self.preview_mode = True
        self.selected_peg = None
        self._automated_turn_id = None
        self._recording_enabled = False
        self._replay_window = None
        self._replay_tooltip = None

        self.size_var = tk.StringVar(value="7")
        self.type_var = tk.StringVar(value="English")
        self.mode_var = tk.StringVar(value=ManualGame.MODE)
        self.record_var = tk.BooleanVar(value=False)
        self.hints_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Choose a board and click Start Game.")
        self.count_var = tk.StringVar()

        # One simple bordered area, like the instruction's example
        window = tk.Frame(root, bg="white", bd=1, relief="solid")
        window.pack(padx=10, pady=10)

        # Board selection on the left
        left = tk.Frame(window, bg="white")
        left.grid(row=0, column=0, sticky="nw", padx=(10, 2), pady=(72, 0))
        tk.Label(left, text="Board Type", bg="white").pack(anchor="w")

        for board_type in Board.TYPES:
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
            right, self.size_var, *(str(size) for size in Board.SIZES),
            command=self.show_preview
        )
        size_menu.config(width=4)
        size_menu.pack(pady=(4, 16))

        tk.Label(right, text="Game Mode", bg="white").pack(anchor="w")
        for mode in (ManualGame.MODE, AutomatedGame.MODE):
            tk.Radiobutton(
                right, text=mode, variable=self.mode_var, value=mode,
                bg="white", activebackground="white"
            ).pack(anchor="w")

        self.record_checkbox = tk.Checkbutton(
            right, text="Record Game", variable=self.record_var,
            bg="white", activebackground="white"
        )
        self.record_checkbox.pack(anchor="w", pady=(8, 0))

        tk.Button(right, text="Start Game", command=self.new_game).pack(fill="x", pady=(12, 0))
        self.replay_button = tk.Button(right, text="Replay", command=self.replay_game)
        self.replay_button.pack(fill="x", pady=(8, 0))
        self.replay_button.bind("<Enter>", self._show_replay_tooltip)
        self.replay_button.bind("<Leave>", self._hide_replay_tooltip)
        self.undo_button = tk.Button(right, text="Undo", command=self.undo_move)
        self.undo_button.pack(fill="x", pady=(8, 0))
        self.randomize_button = tk.Button(right, text="Randomize", command=self.randomize_board)
        self.randomize_button.pack(fill="x", pady=(8, 0))

        # Basic text at the bottom
        tk.Label(window, textvariable=self.status_var, bg="white").grid(
            row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 2)
        )
        tk.Label(window, textvariable=self.count_var, bg="white").grid(
            row=2, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 10)
        )

        self.draw_board()

    def show_preview(self, *args):
        self._cancel_automated_turn()
        self._recording_enabled = False
        self.preview_board = Board(int(self.size_var.get()), self.type_var.get())
        self.preview_mode = True
        self.selected_peg = None
        self.status_var.set("Board preview. Click Start Game to play.")
        self.draw_board()

    def new_game(self):
        self._cancel_automated_turn()
        game_class = AutomatedGame if self.mode_var.get() == AutomatedGame.MODE else ManualGame
        self.game = game_class(int(self.size_var.get()), self.type_var.get())
        self.preview_mode = False
        self.selected_peg = None
        self._recording_enabled = self.record_var.get()
        self._write_recording()
        if isinstance(self.game, AutomatedGame):
            self.status_var.set("Automated game in progress.")
            self._schedule_automated_turn()
        else:
            self.status_var.set("Select a peg, then an empty hole.")
        self.draw_board()

    def _schedule_automated_turn(self):
        self._automated_turn_id = self.root.after(
            self.AUTOMATED_TURN_DELAY_MS, self._play_automated_turn
        )

    def _cancel_automated_turn(self):
        if self._automated_turn_id is not None:
            self.root.after_cancel(self._automated_turn_id)
            self._automated_turn_id = None

    def _play_automated_turn(self):
        self._automated_turn_id = None
        if self.game.play_turn():
            self._write_recording()
        if self.game.is_game_over():
            self.show_result()
        else:
            self._schedule_automated_turn()
        self.draw_board()

    def undo_move(self):
        if self.preview_mode or not isinstance(self.game, ManualGame):
            return

        if self.game.undo_move():
            self.selected_peg = None
            self.record_var.set(self._recording_enabled)
            self._write_recording()
            self.status_var.set("Last move undone.")
            self.draw_board()
        else:
            self.status_var.set("Nothing to undo.")

    def randomize_board(self):
        if self.preview_mode or not isinstance(self.game, ManualGame):
            return
        if not self.game.randomize_board():
            return

        self.selected_peg = None
        self._write_recording()
        if self.game.is_game_over():
            self.show_result()
        else:
            self.status_var.set("Board randomized. Select a peg, then an empty hole.")
        self.draw_board()

    def _write_recording(self):
        if not self._recording_enabled:
            return

        try:
            self.game.save_recording(self.RECORDING_PATH)
        except OSError as error:
            self._recording_enabled = False
            self.record_var.set(False)
            messagebox.showerror(
                "Could not update recording.txt",
                f"Recording stopped for this game.\n\n{error}",
                parent=self.root,
            )

    def _show_replay_tooltip(self, event):
        if self._replay_tooltip is not None:
            return

        tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        tk.Label(
            tip,
            text="Will replay the most recently recorded game",
            bg="#ffffe0",
            relief="solid",
            bd=1,
            padx=6,
            pady=3,
        ).pack()
        tip.update_idletasks()
        button = event.widget
        x = min(button.winfo_rootx(), button.winfo_screenwidth() - tip.winfo_reqwidth())
        y = button.winfo_rooty() + button.winfo_height() + 4
        tip.geometry(f"+{max(0, x)}+{y}")
        self._replay_tooltip = tip

    def _hide_replay_tooltip(self, event=None):
        if self._replay_tooltip is not None:
            self._replay_tooltip.destroy()
            self._replay_tooltip = None

    def replay_game(self):
        self._hide_replay_tooltip()
        try:
            mode, boards = load_recording(self.RECORDING_PATH)
        except FileNotFoundError:
            messagebox.showinfo(
                "No recording yet",
                "Check Record Game and start a game to make a recording.",
                parent=self.root,
            )
            return
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not replay recording.txt", str(error), parent=self.root)
            return

        if self._replay_window is not None:
            self._replay_window.destroy()

        window = tk.Toplevel(self.root)
        window.title(f"Peg Solitaire - {mode} Replay")
        window.transient(self.root)
        window.resizable(False, False)
        self._replay_window = window

        canvas = tk.Canvas(window, width=350, height=330, bg="white", highlightthickness=0)
        canvas.pack()
        progress = tk.Label(window)
        progress.pack(padx=10, pady=(0, 10))

        next_frame = None

        def show_frame(index):
            nonlocal next_frame
            next_frame = None
            board = boards[index]
            self._draw_board(canvas, board)
            peg_count = board.peg_count()
            if index + 1 < len(boards):
                progress.config(text=f"Replay {index + 1} of {len(boards)} | Pegs remaining: {peg_count}")
                next_frame = window.after(self.REPLAY_FRAME_DELAY_MS, show_frame, index + 1)
            else:
                progress.config(text=f"Replay complete | Pegs remaining: {peg_count}")

        def cancel_playback(event):
            if event.widget is window:
                if next_frame is not None:
                    window.after_cancel(next_frame)
                self._replay_window = None

        window.bind("<Destroy>", cancel_playback)
        show_frame(0)

    def draw_board(self):
        board = self.preview_board if self.preview_mode else self.game.board
        hints = set()
        if self.hints_var.get() and not self.preview_mode and self.selected_peg is not None:
            for move in self.game.get_valid_moves():
                if (move.start_row, move.start_col) == self.selected_peg:
                    hints.add((move.end_row, move.end_col))

        self._draw_board(self.canvas, board, self.selected_peg, hints)
        self.canvas.tag_bind("cell", "<Button-1>", self.on_cell_click)
        self.count_var.set(f"Pegs remaining: {board.peg_count()}")
        manual_game_active = not self.preview_mode and isinstance(self.game, ManualGame)
        game_in_progress = not self.preview_mode and not self.game.is_game_over()
        self.undo_button.config(state="normal" if manual_game_active else "disabled")
        can_randomize = manual_game_active and game_in_progress
        self.randomize_button.config(state="normal" if can_randomize else "disabled")
        self.record_checkbox.config(state="disabled" if game_in_progress else "normal")

    @staticmethod
    def _draw_board(canvas, board, selected_peg=None, hints=()):
        canvas.delete("all")
        center = board.size // 2
        spacing = min(38, 300 / board.size)
        center_x, center_y = 175, 165

        for row in range(board.size):
            for col in range(board.size):
                cell = board.get_cell(row, col)
                if cell == Board.INVALID:
                    continue

                selected = (row, col) == selected_peg
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
                    canvas.create_polygon(points, fill=fill, outline="black", tags=tags)
                else:
                    x = center_x + (col - center) * spacing
                    y = center_y + (row - center) * spacing
                    half = spacing / 2
                    canvas.create_rectangle(
                        x - half, y - half, x + half, y + half,
                        fill=fill, outline="black", tags=tags
                    )

                peg_radius = spacing * 0.30
                color = "black" if cell == Board.PEG else "white"
                canvas.create_oval(
                    x - peg_radius, y - peg_radius,
                    x + peg_radius, y + peg_radius,
                    fill=color, outline="black", tags=tags
                )

    def on_cell_click(self, event):
        if self.preview_mode:
            self.status_var.set("Click Start Game before playing.")
            return
        if isinstance(self.game, AutomatedGame):
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
                self._write_recording()
                if self.game.is_game_over():
                    self.show_result()
                else:
                    self.status_var.set("Move made.")
            else:
                self.status_var.set("Invalid move.")

        self.draw_board()

    def show_result(self):
        if isinstance(self.game, ManualGame):
            self.status_var.set(f"Game over! Rating: {self.game.get_rating()}.")
        else:
            self.status_var.set("Game over!")
