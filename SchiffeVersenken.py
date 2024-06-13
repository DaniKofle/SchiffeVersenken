import tkinter as tk
from tkinter import messagebox



class ShipGamePlayer(tk.Tk):
    def __init__(self, size=10, ships=[(4, "Flugzeugträger"), (3, "Schlachtschiff"), (2, "U-Boot"), (1, "Fischerboot")], player=1, placement_callback=None):
        super().__init__()
        self.size = size
        self.ships = ships
        self.player = player
        self.title(f"Spieler {self.player}: Schiffe platzieren")
        self.current_ship_index = 0
        self.current_ship_size, self.current_ship_name = self.ships[self.current_ship_index]
        self.placedships_board = [["O" for _ in range(self.size)] for _ in range(self.size)]
        self.ship_positions = {name: [] for _, name in self.ships}
        self.placement_callback = placement_callback
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
                self.buttons[x + i][y].config(bg="red" if self.player == 1 else "blue")
                positions.append((x + i, y))
            elif y + size <= self.size:
                self.placedships_board[x][y + i] = "S"
                self.buttons[x][y + i].config(bg="red" if self.player == 1 else "blue")
                positions.append((x, y + i))
        self.ship_positions[self.current_ship_name] = positions
        if all(len(row) == self.size and row.count("S") == size for row in self.placedships_board):
            messagebox.showinfo("Fertig!", f"Spieler {self.player} hat alle Schiffe platziert.")
            self.destroy()
            if self.placement_callback:
                self.placement_callback(self.player, self.placedships_board, self.ship_positions)

    def next_ship(self):
        self.current_ship_index += 1
        if self.current_ship_index < len(self.ships):
            self.current_ship_size, self.current_ship_name = self.ships[self.current_ship_index]
            self.info_label.config(text=f"Platziere dein {self.current_ship_name} ({self.current_ship_size} Felder)")
        else:
            messagebox.showinfo("Fertig!", f"Spieler {self.player} hat alle Schiffe platziert.")
            self.destroy()
            if self.placement_callback:
                self.placement_callback(self.player, self.placedships_board, self.ship_positions)


class GamePhase:
    def __init__(self, size=10, player1_board=None, player2_board=None, player1_ships=None, player2_ships=None):
        self.size = size
        self.player1_board = player1_board
        self.player2_board = player2_board
        self.player1_ships = player1_ships
        self.player2_ships = player2_ships
        self.current_player = 1
        self.player1_hits = 0
        self.player2_hits = 0

    def start_game(self):
        self.start_player_turn()

    def start_player_turn(self):
        if self.current_player == 1:
            self.player_guess_window = tk.Tk()
            self.player_guess_window.title("Spieler 1: Schiffe erraten")
            self.create_guess_board(self.player_guess_window, self.player2_board, self.player1_turn)
        else:
            self.player_guess_window = tk.Tk()
            self.player_guess_window.title("Spieler 2: Schiffe erraten")
            self.create_guess_board(self.player_guess_window, self.player1_board, self.player2_turn)
        self.player_guess_window.mainloop()

    def player1_turn(self, x, y, btn):
        if self.player2_board[x][y] == "S":
            btn.config(bg="blue")
            messagebox.showinfo("Treffer!", "Versenkt!")
            self.player2_board[x][y] = "H"
            self.player1_hits += 1
            ship_name = self.check_sunk_ship(x, y, self.player2_ships)
            if ship_name:
                messagebox.showinfo("Versenkt!", f"{ship_name} versenkt!")
            if self.check_win(self.player1_hits):
                messagebox.showinfo("Spieler 1 gewinnt!", "Alle Schiffe von Spieler 2 sind versenkt!")
                self.player_guess_window.destroy()
            else:
                self.current_player = 1  # Player 1 geht weiter
                self.player_guess_window.destroy()
                self.start_player_turn()
        elif self.player2_board[x][y] == "O":
            btn.config(bg="black")
            messagebox.showinfo("Fehler!", "Verfehlt")
            self.player2_board[x][y] = "M"  # als Verfehlt markieren
            self.current_player = 2  # player 2 geht weiter
            self.player_guess_window.destroy()
            self.start_player_turn()

    def player2_turn(self, x, y, btn):
        if self.player1_board[x][y] == "S":
            btn.config(bg="red")
            messagebox.showinfo("Treffer!", "Versenkt!")
            self.player1_board[x][y] = "H"
            self.player2_hits += 1
            ship_name = self.check_sunk_ship(x, y, self.player1_ships)
            if ship_name:
                messagebox.showinfo("Versenkt!", f"{ship_name} versenkt!")
            if self.check_win(self.player2_hits):
                messagebox.showinfo("Spieler 2 gewinnt!", "Alle Schiffe von Spieler 1 sind versenkt!")
                self.player_guess_window.destroy()
            else:
                self.current_player = 2  # Spieler 2 geht weiter
                self.player_guess_window.destroy()
                self.start_player_turn()
        elif self.player1_board[x][y] == "O":
            btn.config(bg="black")
            messagebox.showinfo("Fehler!", "Verfehlt")
            self.player1_board[x][y] = "M"  # Mark as miss
            self.current_player = 1  # Spielerwechsel
            self.player_guess_window.destroy()
            self.start_player_turn()

    def create_guess_board(self, window, board, turn_callback):
        for i in range(self.size):
            for j in range(self.size):
                btn = tk.Button(window, text="", width=2, height=1)
                btn.grid(row=i, column=j)
                if board[i][j] == "H":
                    if board == self.player2_board:
                        btn.config(bg="blue")
                    else:
                        btn.config(bg="red")
                elif board[i][j] == "M":
                    btn.config(bg="black")
                else:
                    btn.config(command=lambda x=i, y=j, b=btn: turn_callback(x, y, b))

    def check_win(self, hits):
        total_ship_cells = sum(ship[0] for ship in [(4, "Flugzeugträger"), (3, "Schlachtschiff"), (2, "U-Boot"), (1, "Fischerboot")])
        return hits == total_ship_cells

    def check_sunk_ship(self, x, y, ships):
        for ship_name, coordinates in ships.items():
            if (x, y) in coordinates:
                coordinates.remove((x, y))
                if not coordinates:
                    return ship_name
        return None


if __name__ == "__main__":
    player1_board = []
    player2_board = []
    player1_ships = {}
    player2_ships = {}

    def start_game_phase(player, board, ships):
        global player1_board, player2_board, player1_ships, player2_ships
        if player == 1:
            player1_board = board
            player1_ships = ships
            start_ship_placement_for_player2()
        elif player == 2:
            player2_board = board
            player2_ships = ships
            game_phase = GamePhase(size=10, player1_board=player1_board, player2_board=player2_board, player1_ships=player1_ships, player2_ships=player2_ships)
            game_phase.start_game()

    def start_ship_placement_for_player2():
        player2 = ShipGamePlayer(player=2, placement_callback=start_game_phase)
        player2.mainloop()

    def start_ship_placement_for_player1():
        player1 = ShipGamePlayer(player=1, placement_callback=start_game_phase)
        player1.mainloop()

    start_ship_placement_for_player1()
 