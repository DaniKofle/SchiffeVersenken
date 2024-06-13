import socket
import threading
import tkinter as tk
from tkinter import messagebox

class ShipGameServer(tk.Tk):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        self.conn, self.addr = None, None
        
        self.size = 10
        self.ships = [(4, "Flugzeugträger"), (3, "Schlachtschiff"), (2, "U-Boot"), (1, "Fischerboot")]
        self.player = 1
        self.current_ship_index = 0
        self.current_ship_size, self.current_ship_name = self.ships[self.current_ship_index]
        self.placedships_board = [["O" for _ in range(self.size)] for _ in range(self.size)]
        self.ship_positions = {name: [] for _, name in self.ships}
        self.create_widgets()
        
        threading.Thread(target=self.wait_for_connection, daemon=True).start()

    def wait_for_connection(self):
        self.conn, self.addr = self.sock.accept()
        print(f"Connected by {self.addr}")
        threading.Thread(target=self.receive_data, daemon=True).start()

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

    def place_ship(self, x, y):
        if self.can_place_ship(self.current_ship_size, x, y):
            self.mark_ship(self.current_ship_size, x, y)
            self.next_ship()

    def can_place_ship(self, size, x, y):
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

    def mark_ship(self, size, x, y):
        positions = []
        for i in range(size):
            if x + size <= self.size:
                self.placedships_board[x + i][y] = "S"
                self.buttons[x + i][y].config(bg="red")
                positions.append((x + i, y))
            elif y + size <= self.size:
                self.placedships_board[x][y + i] = "S"
                self.buttons[x][y + i].config(bg="red")
                positions.append((x, y + i))
        self.ship_positions[self.current_ship_name] = positions
        self.check_all_ships_placed()

    def next_ship(self):
        self.current_ship_index += 1
        if self.current_ship_index < len(self.ships):
            self.current_ship_size, self.current_ship_name = self.ships[self.current_ship_index]
            self.info_label.config(text=f"Platziere dein {self.current_ship_name} ({self.current_ship_size} Felder)")
        else:
            self.check_all_ships_placed()

    def check_all_ships_placed(self):
        if self.current_ship_index >= len(self.ships):
            messagebox.showinfo("Fertig!", f"Spieler {self.player} hat alle Schiffe platziert.")
            self.send_data("PLACEMENT", self.placedships_board, self.ship_positions)
            self.destroy()

    def send_data(self, data_type, board, positions):
        if self.conn:
            data = f"{data_type}|{board}|{positions}"
            self.conn.sendall(data.encode())

    def receive_data(self):
        while True:
            data = self.conn.recv(1024).decode()
            if not data:
                break
            data_type, board, positions = data.split("|")
            if data_type == "PLACEMENT":
                self.start_game_phase(board, positions)

    def start_game_phase(self, board, positions):
        self.player2_board = eval(board)
        self.player2_ships = eval(positions)
        self.start_game()

    def start_game(self):
        self.player_guess_window = tk.Tk()
        self.player_guess_window.title("Spieler 1: Schiffe erraten")
        self.create_guess_board(self.player_guess_window, self.player2_board, self.player1_turn)
        self.player_guess_window.mainloop()

    def player1_turn(self, x, y, btn):
        if self.player2_board[x][y] == "S":
            btn.config(bg="blue")
            messagebox.showinfo("Treffer!", "Versenkt!")
            self.player2_board[x][y] = "H"
            ship_name = self.check_sunk_ship(x, y, self.player2_ships)
            if ship_name:
                messagebox.showinfo("Versenkt!", f"{ship_name} versenkt!")
            self.send_data("HIT", self.player2_board, (x, y))
            if self.check_win():
                messagebox.showinfo("Spieler 1 gewinnt!", "Alle Schiffe von Spieler 2 sind versenkt!")
                self.player_guess_window.destroy()
            else:
                self.player_guess_window.destroy()
                self.start_game()
        elif self.player2_board[x][y] == "O":
            btn.config(bg="black")
            messagebox.showinfo("Fehler!", "Verfehlt")
            self.player2_board[x][y] = "M"
            self.send_data("MISS", self.player2_board, (x, y))
            self.player_guess_window.destroy()
            self.start_game()

    def create_guess_board(self, window, board, turn_callback):
        for i in range(self.size):
            for j in range(self.size):
                btn = tk.Button(window, text="", width=2, height=1)
                btn.grid(row=i, column=j)
                if board[i][j] == "H":
                    btn.config(bg="blue")
                elif board[i][j] == "M":
                    btn.config(bg="black")
                else:
                    btn.config(command=lambda x=i, y=j, b=btn: turn_callback(x, y, b))

    def check_win(self):
        total_ship_cells = sum(ship[0] for ship in self.ships)
        player1_hits = sum(row.count("H") for row in self.player2_board)
        return player1_hits == total_ship_cells

    def check_sunk_ship(self, x, y, ships):
        for ship_name, coordinates in ships.items():
            if (x, y) in coordinates:
                coordinates.remove((x, y))
                if not coordinates:
                    return ship_name
        return None

if __name__ == "__main__":
    host = 'localhost'
    port = 5000
    server = ShipGameServer(host, port)
    server.mainloop()
