import socket
import threading
import tkinter as tk
from tkinter import messagebox
import pickle

class BattleshipClient:
    def __init__(self, host='192.168.5.179', port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.player_color = None
        self.opponent_ship_positions = None
        self.is_my_turn = False
        self.guess_buttons = []
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
                if msg.startswith("COLOR:"):
                    self.player_color = msg.split(":")[1]
                elif msg.startswith("OPPONENT_SHIP_POSITIONS:"):
                    self.opponent_ship_positions = msg[len("OPPONENT_SHIP_POSITIONS:"):]
                    print(f"Received opponent's ship positions: {self.opponent_ship_positions}")  # Debug-Ausgabe im Client
                    self.start_guessing_phase()
                elif msg.startswith("TURN:"):
                    self.is_my_turn = True if msg.split(":")[1] == "YES" else False
                    if self.is_my_turn:
                        self.guess_window.deiconify()
                elif msg.startswith("RESULT:"):
                    self.process_result(msg[len("RESULT:"):])
                else:
                    print(msg)
            except:
                break

    def start_guessing_phase(self):
        self.guess_window = tk.Toplevel(self.window)
        self.guess_window.title("Battleship - Guess Opponent's Ships")
        self.guess_buttons = []

        for row in range(self.grid_size):
            button_row = []
            for col in range(self.grid_size):
                button = tk.Button(self.guess_window, width=2, height=1, command=lambda r=row, c=col: self.make_guess(r, c))
                button.grid(row=row, column=col)
                button_row.append(button)
            self.guess_buttons.append(button_row)

        self.guess_window.withdraw()  # Hide the guess window initially

    def make_guess(self, row, col):
        if self.is_my_turn:
            self.client.sendall(f"GUESS:{row}:{col}".encode())
            self.is_my_turn = False  # Disable further guesses until the next turn

    def process_result(self, result):
        row, col, hit = result.split(",")
        row, col = int(row), int(col)
        if hit == "HIT":
            self.guess_buttons[row][col].config(bg='red')
            messagebox.showinfo("Result", "Treffer!")
            self.is_my_turn = True  # Allow the player to guess again
        else:
            self.guess_buttons[row][col].config(bg='black')
            messagebox.showinfo("Result", "Verfehlt!")

if __name__ == "__main__":
    client = BattleshipClient()

