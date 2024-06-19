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
        self.guess_buttons1 = []  # Updated variable for player 1 guess buttons
        self.guess_buttons2 = []  # Updated variable for player 2 guess buttons
        self.local_guesses_player_1 = []  # Local storage for player 1 guesses
        self.local_guesses_player_2 = []  # Local storage for player 2 guesses
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
            self.window.after(2000, self.window.destroy)  # Close the window after 2 seconds

    def send_ship_positions(self):
        positions_str = ",".join([f"{r}:{c}" for r, c in self.all_ship_positions])
        print(f"Sending ship positions to server: {positions_str}")  # Debug-Ausgabe im Client
        self.client.sendall(f"SHIP_POSITIONS:{positions_str}".encode())

    def receive_messages(self):
        while True:
            try:
                msg = self.client.recv(1024).decode()
                messages = msg.split("WELCOME:")
                for m in messages:
                    if m.startswith("COLOR:"):
                        self.player_color = m.split(":")[1]
                        print(f"Set player_color to {self.player_color}")  # Debug-Ausgabe
                    elif m.startswith("PLAYER_ID:"):
                        self.player_id = int(m.split(":")[1])
                        print(f"Set player_id to {self.player_id}")  # Debug-Ausgabe
                        self.check_start_guessing_phase()  # Überprüfen, ob die Ratephase gestartet werden kann
                    elif "Welcome" in m:
                        print(f"Welcome message: {m}")  # Print the welcome message
                    elif m.startswith("OPPONENT_SHIP_POSITIONS:"):
                        self.opponent_ship_positions = [tuple(map(int, pos.split(":"))) for pos in m[len("OPPONENT_SHIP_POSITIONS:"):].split(",")]
                        print(f"Received opponent's ship positions: {self.opponent_ship_positions}")  # Debug-Ausgabe im Client
                        self.received_opponent_positions = True
                        self.check_start_guessing_phase()  # Überprüfen, ob die Ratephase gestartet werden kann
                    elif m.startswith("TURN:"):
                        self.is_my_turn = True if m.split(":")[1] == "YES" else False
                        print(f"Set is_my_turn to {self.is_my_turn}")  # Debug-Ausgabe
                        self.update_guess_window()
                    elif m.startswith("RESULT:"):
                        self.process_result(m[len("RESULT:"):])
                    else:
                        print(m)
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
            self.guess_buttons1 = self.create_guess_buttons(self.guess_window_player_1, 1)

            print("Guess window for player 1 created")  # Debug-Ausgabe
            self.guess_window_player_1.withdraw()  # Fenster zunächst ausblenden

        if self.player_id == 2 and self.guess_window_player_2 is None:
            print("Creating guess window for player 2")  # Debug-Ausgabe
            self.guess_window_player_2 = tk.Toplevel(self.window)
            self.guess_window_player_2.title("Battleship - Player 2 Guessing Board")
            self.guess_buttons2 = self.create_guess_buttons(self.guess_window_player_2, 2)

            print("Guess window for player 2 created")  # Debug-Ausgabe
            self.guess_window_player_2.withdraw()  # Fenster zunächst ausblenden

        self.update_guess_window()

    def create_guess_buttons(self, guess_window, player_id):
        guess_buttons = []
        for row in range(self.grid_size):
            button_row = []
            for col in range(self.grid_size):
                button = tk.Button(guess_window, width=2, height=1, command=lambda r=row, c=col: self.make_guess(r, c, player_id))
                button.grid(row=row, column=col)
                button_row.append(button)
            guess_buttons.append(button_row)
        return guess_buttons

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

    def make_guess(self, row, col, player_id):
        guess = (row, col)
        if player_id == 1:
            if guess not in self.local_guesses_player_1:
                self.local_guesses_player_1.append(guess)
                hit = guess in self.opponent_ship_positions
                self.guess_buttons1[row][col].config(state='disabled', bg='blue' if hit else 'black')
                self.client.sendall(f"GUESS:{row}:{col}".encode())
                self.show_result_message(hit)
        elif player_id == 2:
            if guess not in self.local_guesses_player_2:
                self.local_guesses_player_2.append(guess)
                hit = guess in self.opponent_ship_positions
                self.guess_buttons2[row][col].config(state='disabled', bg='blue' if hit else 'black')
                self.client.sendall(f"GUESS:{row}:{col}".encode())
                self.show_result_message(hit)

    def show_result_message(self, hit):
        if hit:
            messagebox.showinfo("Result", "Treffer!")
        else:
            messagebox.showinfo("Result", "Verfehlt!")

    def process_result(self, result):
        # Placeholder for processing results received from the server
        pass

if __name__ == "__main__":
    client = BattleshipClient()

