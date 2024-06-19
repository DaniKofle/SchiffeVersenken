import socket
import threading
import tkinter as tk
from tkinter import messagebox
import pickle

class BattleshipClient:
    def __init__(self, host='192.168.5.179', port=5555):
        print("Initializing BattleshipClient...")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.player_id = None  # New attribute to identify player (1 or 2)
        self.player_color = None  # Player color
        self.opponent_ship_positions = []
        self.is_my_turn = False
        self.guess_window_player_1 = None
        self.guess_window_player_2 = None
        self.guess_buttons_player_1 = []
        self.guess_buttons_player_2 = []
        self.received_opponent_positions = False
        threading.Thread(target=self.receive_messages).start()

        self.window = tk.Tk()
        self.window.title("Battleship - Place Your Ships")

        self.grid_size = 10
        self.ship_sizes = [4, 3, 2, 1]  # Flugzeugträger, Kreuzer, Schiff, Fischerboot
        self.ship_names = ["Flugzeugträger", "Kreuzer", "Schiff", "Fischerboot"]
        self.current_ship_index = 0
        self.all_ship_positions = []

        self.create_widgets()
        self.window.mainloop()

    def create_widgets(self):
        self.buttons = []
        for row in range(self.grid_size):
            button_row = []
            for col in range(self.grid_size):
                button = tk.Button(self.window, width=2, height=1, command=lambda r=row, c=col: self.place_ship(r, c))
                button.grid(row=row, column=col)
                button_row.append(button)
            self.buttons.append(button_row)

        self.info_label = tk.Label(self.window, text=f"Place your {self.ship_names[self.current_ship_index]} of size {self.ship_sizes[self.current_ship_index]}")
        self.info_label.grid(row=self.grid_size, column=0, columnspan=self.grid_size)

    def place_ship(self, row, col):
        ship_size = self.ship_sizes[self.current_ship_index]
        if row + ship_size > self.grid_size:
            messagebox.showerror("Error", f"Cannot place {self.ship_names[self.current_ship_index]} here.")
            return

        self.ship_positions = [(row + i, col) for i in range(ship_size)]
        for r, c in self.ship_positions:
            self.buttons[r][c].config(bg=self.player_color, state='disabled')

        self.all_ship_positions.extend(self.ship_positions)
        self.current_ship_index += 1

        if self.current_ship_index < len(self.ship_sizes):
            self.info_label.config(text=f"Place your {self.ship_names[self.current_ship_index]} of size {self.ship_sizes[self.current_ship_index]}")
        else:
            self.info_label.config(text="All ships placed! Waiting for other player...")
            self.send_ship_positions()
            for row in self.buttons:
                for button in row:
                    button.config(state='disabled')

    def send_ship_positions(self):
        positions_str = ",".join([f"{r}:{c}" for r, c in self.all_ship_positions])
        print(f"Sending ship positions to server: {positions_str}")  # Debug-Ausgabe im Client
        self.client.sendall(f"SHIP_POSITIONS:{positions_str}".encode())

    def receive_messages(self):
        while True:
            try:
                msg = self.client.recv(1024).decode()
                print(f"Received message: {msg}")  # Debug-Ausgabe
                if msg.startswith("PLAYER_ID:"):
                    self.player_id = int(msg.split(":")[1])
                    print(f"Set player_id to {self.player_id}")  # Debug-Ausgabe
                    self.check_start_guessing_phase()  # Überprüfen, ob die Ratephase gestartet werden kann
                elif msg.startswith("COLOR:"):
                    self.player_color = msg.split(":")[1]
                    print(f"Set player_color to {self.player_color}")  # Debug-Ausgabe
                elif msg.startswith("WELCOME:"):
                    print(msg)  # Print the welcome message
                elif msg.startswith("OPPONENT_SHIP_POSITIONS:"):
                    self.opponent_ship_positions = [tuple(map(int, pos.split(":"))) for pos in msg[len("OPPONENT_SHIP_POSITIONS:"):].split(",")]
                    print(f"Received opponent's ship positions: {self.opponent_ship_positions}")  # Debug-Ausgabe im Client
                    self.received_opponent_positions = True
                    self.check_start_guessing_phase()  # Überprüfen, ob die Ratephase gestartet werden kann
                elif msg.startswith("TURN:"):
                    self.is_my_turn = True if msg.split(":")[1] == "YES" else False
                    print(f"Set is_my_turn to {self.is_my_turn}")  # Debug-Ausgabe
                    self.update_guess_window()
                elif msg.startswith("RESULT:"):
                    self.process_result(msg[len("RESULT:"):])
                else:
                    print(msg)
            except Exception as e:
                print(f"Error: {e}")
                break

    def check_start_guessing_phase(self):
        if self.player_id is not None and self.received_opponent_positions:
            self.start_guessing_phase()

    def start_guessing_phase(self):
        print(f"Starting guessing phase for player {self.player_id}...")  # Debug-Ausgabe
        if self.player_id == 1 and self.guess_window_player_1 is None:
            print("Creating guess window for player 1")  # Debug-Ausgabe
            self.guess_window_player_1 = tk.Toplevel(self.window)
            self.guess_window_player_1.title("Battleship - Player 1 Guessing Board")
            self.guess_buttons_player_1 = []

            for row in range(self.grid_size):
                button_row = []
                for col in range(self.grid_size):
                    button = tk.Button(self.guess_window_player_1, width=2, height=1, command=lambda r=row, c=col: self.make_guess(r, c))
                    button.grid(row=row, column=col)
                    button_row.append(button)
                self.guess_buttons_player_1.append(button_row)

            print("Guess window for player 1 created")  # Debug-Ausgabe
            self.guess_window_player_1.withdraw()  # Fenster zunächst ausblenden

        if self.player_id == 2 and self.guess_window_player_2 is None:
            print("Creating guess window for player 2")  # Debug-Ausgabe
            self.guess_window_player_2 = tk.Toplevel(self.window)
            self.guess_window_player_2.title("Battleship - Player 2 Guessing Board")
            self.guess_buttons_player_2 = []

            for row in range(self.grid_size):
                button_row = []
                for col in range(self.grid_size):
                    button = tk.Button(self.guess_window_player_2, width=2, height=1, command=lambda r=row, c=col: self.make_guess(r, c))
                    button.grid(row=row, column=col)
                    button_row.append(button)
                self.guess_buttons_player_2.append(button_row)

            print("Guess window for player 2 created")  # Debug-Ausgabe
            self.guess_window_player_2.withdraw()  # Fenster zunächst ausblenden

        self.update_guess_window()

    def update_guess_window(self):
        if self.player_id is None:
            print("Player ID is not set. Skipping update_guess_window.")  # Debug-Ausgabe
            return

        print(f"Updating guess window for player {self.player_id}, is_my_turn: {self.is_my_turn}")  # Debug-Ausgabe
        if self.player_id == 1 and self.guess_window_player_1 is not None:
            print("Updating guess window for player 1")  # Debug-Ausgabe
            if self.is_my_turn:
                print("Player 1's turn, showing guess window")  # Debug-Ausgabe
                self.guess_window_player_1.deiconify()
            else:
                print("Not player 1's turn, hiding guess window")  # Debug-Ausgabe
                self.guess_window_player_1.withdraw()

        elif self.player_id == 2 and self.guess_window_player_2 is not None:
            print("Updating guess window for player 2")  # Debug-Ausgabe
            if self.is_my_turn:
                print("Player 2's turn, showing guess window")  # Debug-Ausgabe
                self.guess_window_player_2.deiconify()
            else:
                print("Not player 2's turn, hiding guess window")  # Debug-Ausgabe
                self.guess_window_player_2.withdraw()

    def make_guess(self, row, col):
        if self.is_my_turn:
            print(f"Making guess: ({row}, {col})")  # Debug-Ausgabe
            self.client.sendall(f"GUESS:{row}:{col}".encode())
            self.is_my_turn = False  # Disable further guesses until the next turn

    def process_result(self, result):
        row, col, hit = result.split(",")
        row, col = int(row), int(col)
        print(f"Processing result: ({row}, {col}), hit: {hit}")  # Debug-Ausgabe
        if self.player_id == 1:
            guess_buttons = self.guess_buttons_player_1
        else:
            guess_buttons = self.guess_buttons_player_2

        if hit == "HIT":
            guess_buttons[row][col].config(bg='red')
            messagebox.showinfo("Result", "Treffer!")
            self.is_my_turn = True  # Allow the player to guess again
        else:
            guess_buttons[row][col].config(bg='black')
            messagebox.showinfo("Result", "Verfehlt!")

if __name__ == "__main__":
    client = BattleshipClient()
