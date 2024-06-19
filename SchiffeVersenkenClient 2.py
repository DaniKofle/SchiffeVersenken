import socket
import pickle
import threading
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Tuple

class ShipGamePlayer(tk.Tk):
    def __init__(self, size: int = 10, ships: List[Tuple[int, str]] = None, player: int = 1, connection: socket.socket = None):
        if ships is None:
            ships = [(4, "Flugzeugträger"), (3, "Schlachtschiff"), (2, "U-Boot"), (1, "Fischerboot")]
        super().__init__()
        self.size = size
        self.ships = ships
        self.player = player
        self.connection = connection
        self.current_ship_index = 0
        self.current_ship_size, self.current_ship_name = self.ships[self.current_ship_index]
        self.placedships_board: List[List[str]] = [["O" for _ in range(self.size)] for _ in range(self.size)]
        self.ship_positions: Dict[str, List[Tuple[int, int]]] = {name: [] for _, name in self.ships}
        self.create_widgets()

    def create_widgets(self):
        self.buttons = []
        for i in range(self.size):
            row_buttons = []
            for j in range(self.size):
                btn = tk.Button(self, text="", width=2, height=1, command=lambda x=i, y=j: self.place_ship(x, y))
                btn.grid(row=i, column=j)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        self.info_label = tk.Label(self, text=f"Platziere dein {self.current_ship_name} ({self.current_ship_size} Felder)")
        self.info_label.grid(row=self.size, columnspan=self.size)

    def place_ship(self, x: int, y: int):
        if self.can_place_ship(self.current_ship_size, x, y):
            self.mark_ship(self.current_ship_size, x, y)
            self.next_ship()

    def can_place_ship(self, size: int, x: int, y: int) -> bool:
        if x + size <= self.size:
            for i in range(size):
                if self.placedships_board[x + i][y] != "O":
                    return False
            return True
        elif y + size <= self.size:
            for i in range(size):
                if self.placedships_board[x][y + i] != "O":
                    return False
            return True
        return False

    def mark_ship(self, size: int, x: int, y: int):
        positions = []
        for i in range(size):
            if x + size <= self.size:
                self.placedships_board[x + i][y] = "S"
                self.buttons[x + i][y].config(bg="red" if self.player == 1 else "blue")
                positions.append((x + i, y))
            elif y + size <= self.size:
                self.placedships_board[x][y + i] = "S"
                self.buttons[x][y + i].config(bg="red" if self.player == 1 else "blue")
                positions.append((x, y + i))
        self.ship_positions[self.current_ship_name] = positions
        if all(cell == "S" for row in self.placedships_board for cell in row):
            messagebox.showinfo("Fertig!", f"Spieler {self.player} hat alle Schiffe platziert.")
            self.connection.send(pickle.dumps(("place_ship", (self.placedships_board, self.ship_positions))))
            self.destroy()

    def next_ship(self):
        self.current_ship_index += 1
        if self.current_ship_index < len(self.ships):
            self.current_ship_size, self.current_ship_name = self.ships[self.current_ship_index]
            self.info_label.config(text=f"Platziere dein {self.current_ship_name} ({self.current_ship_size} Felder)")
        else:
            messagebox.showinfo("Fertig!", f"Spieler {self.player} hat alle Schiffe platziert.")
            self.connection.send(pickle.dumps(("place_ship", (self.placedships_board, self.ship_positions))))
            self.destroy()

class GameClient:
    def __init__(self, host: str = '10.10.218.24', port: int = 8080):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.player: int = None
        self.guess_window: tk.Tk = None
        self.guess_buttons: List[List[tk.Button]] = []
        self.guess_board: List[List[str]] = None
        self.my_board: List[List[str]] = None
        self.opponent_board: List[List[str]] = None
        self.current_turn: int = None

    def start(self):
        threading.Thread(target=self.receive_data).start()
        self.start_ship_placement()

    def receive_data(self):
        while True:
            try:
                data = pickle.loads(self.client.recv(4096))
                if data:
                    self.handle_message(data)
            except:
                print("Disconnected from server")
                break

    def handle_message(self, message):
        command, data = message
        if command == "start_game":
            print("Game started. Waiting for turn...")
        elif command == "both_boards_placed":
            print("Both boards placed. Starting the first turn...")
        elif command == "player_turn":
            self.player_turn(data)
        elif command == "guess_result":
            self.update_guess_result(data)
        elif command == "win":
            winner = "Spieler 1" if data == 0 else "Spieler 2"
            messagebox.showinfo("Gewonnen!", f"{winner} hat das Spiel gewonnen!")
            self.client.close()
            exit()
        elif command == "set_guess_board":
            self.opponent_board = data
            self.setup_guess_board()

    def player_turn(self, current_player: int):
        self.current_turn = current_player
        if current_player == self.player:
            print("Your turn to guess.")
            self.start_guess()
        else:
            print("Waiting for opponent's turn.")
            self.disable_guess()

    def update_guess_result(self, data):
        player, x, y, result = data
        color = "black" if result == "miss" else ("red" if self.player == 1 else "blue")
        self.guess_buttons[x][y].config(bg=color)
        if result.startswith("sunk"):
            messagebox.showinfo("Versenkt!", result.split(" ", 1)[1])
        self.opponent_board[x][y] = "H" if result == "hit" else "M"
        if result == "miss" and self.current_turn == self.player:
            self.disable_guess()
        elif result == "hit" and self.current_turn == self.player:
            self.enable_guess()  # Spieler darf weiterraten bei einem Treffer.

    def start_ship_placement(self):
        placement = ShipGamePlayer(player=self.player, connection=self.client)
        placement.mainloop()

    def setup_guess_board(self):
        self.guess_board = [["O" for _ in range(10)] for _ in range(10)]
        self.start_guess()

    def start_guess(self):
        if self.opponent_board is None:
            print("Opponent's board not set yet.")
            return
        self.guess_window = tk.Tk()
        self.guess_window.title(f"Spieler {self.player + 1}: Schiffe erraten")
        self.create_guess_board(self.guess_window)
        self.guess_window.mainloop()

    def create_guess_board(self, window: tk.Tk):
        self.guess_buttons = []
        for i in range(10):
            row_buttons = []
            for j in range(10):
                btn = tk.Button(window, text="", width=2, height=1)
                btn.grid(row=i, column=j)
                if self.guess_board[i][j] == "H":
                    btn.config(bg="red" if self.player == 1 else "blue")
                elif self.guess_board[i][j] == "M":
                    btn.config(bg="black")
                else:
                    btn.config(command=lambda x=i, y=j, b=btn: self.send_guess(x, y, b))
                row_buttons.append(btn)
            self.guess_buttons.append(row_buttons)

    def send_guess(self, x: int, y: int, btn: tk.Button):
        self.client.send(pickle.dumps(("guess", (x, y))))
        btn.config(state="disabled")

    def enable_guess(self):
        if self.guess_window:
            for row in self.guess_buttons:
                for btn in row:
                    if btn.cget('bg') == "":
                        btn.config(state="normal")

    def disable_guess(self):
        if self.guess_window:
            for row in self.guess_buttons:
                for btn in row:
                    btn.config(state="disabled")

if __name__ == "__main__":
    player_num = int(input("Enter player number (1 or 2): ")) - 1
    client = GameClient()
    client.player = player_num
    client.start()
