import socket
import threading
import tkinter as tk
from tkinter import messagebox

class BattleshipClient:
    def __init__(self, host='127.0.0.1', port=5555):
        print("Initializing BattleshipClient...")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

        self.player_id = None
        self.player_color = None
        self.opponent_ship_positions = []
        self.is_my_turn = False
        self.grid_size = 10
        self.ship_sizes = [4, 3, 2, 1]
        self.ship_names = ["Flugzeugträger", "Kreuzer", "Schiff", "Fischerboot"]
        self.current_ship_index = 0
        self.all_ship_positions = []

        threading.Thread(target=self.receive_messages).start()

        self.window = tk.Tk()
        self.window.title("Battleship - Place Your Ships")

        self.create_widgets()
        self.create_guess_window()
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

    def create_guess_window(self):
        self.guess_window = tk.Toplevel(self.window)
        self.guess_window.title("Battleship - Guessing Board")

        self.guess_buttons = []
        for row in range(self.grid_size):
            button_row = []
            for col in range(self.grid_size):
                button = tk.Button(self.guess_window, width=2, height=1, command=lambda r=row, c=col: self.make_guess(r, c))
                button.grid(row=row, column=col)
                button_row.append(button)
            self.guess_buttons.append(button_row)

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
        print(f"Sending ship positions to server: {positions_str}")
        self.client.sendall(f"SHIP_POSITIONS:{positions_str}\n".encode())

    def receive_messages(self):
        buffer = ""
        while True:
            try:
                buffer += self.client.recv(1024).decode()
                while '\n' in buffer:
                    msg, buffer = buffer.split('\n', 1)
                    self.handle_message(msg)
            except Exception as e:
                print(f"Error: {e}")
                break

    def handle_message(self, msg):
        if msg.startswith("PLAYER_ID:"):
            self.player_id = int(msg.split(":")[1])
            print(f"Set player_id to {self.player_id}")
        elif msg.startswith("COLOR:"):
            self.player_color = msg.split(":")[1]
            print(f"Set player_color to {self.player_color}")
        elif msg.startswith("WELCOME:"):
            print(msg)
        elif msg.startswith("OPPONENT_SHIP_POSITIONS:"):
            self.opponent_ship_positions = [tuple(map(int, pos.split(":"))) for pos in msg[len("OPPONENT_SHIP_POSITIONS:"):].split(",")]
            print(f"Received opponent's ship positions: {self.opponent_ship_positions}")
        elif msg.startswith("TURN:"):
            self.is_my_turn = True if msg.split(":")[1] == "YES" else False
            print(f"Set is_my_turn to {self.is_my_turn}")
            self.update_guess_window()
        elif msg.startswith("RESULT:"):
            self.process_result(msg[len("RESULT:"):])
        elif msg.startswith("HIT_ON_SHIP:"):
            self.mark_hit_on_ship(msg[len("HIT_ON_SHIP:"):])
        else:
            print(msg)

    def update_guess_window(self):
        if self.is_my_turn:
            for row in self.guess_buttons:
                for button in row:
                    button.config(state='normal')
        else:
            for row in self.guess_buttons:
                for button in row:
                    button.config(state='disabled')

    def make_guess(self, row, col):
        if self.is_my_turn:
            print(f"Making guess: ({row}, {col})")
            self.client.sendall(f"GUESS:{row}:{col}\n".encode())
            self.is_my_turn = False

    def process_result(self, result):
        row, col, hit = result.split(",")
        row, col = int(row), int(col)
        print(f"Processing result: ({row}, {col}), hit: {hit}")

        if hit == "HIT":
            self.guess_buttons[row][col].config(bg='red')
            messagebox.showinfo("Result", "Treffer!")
        else:
            self.guess_buttons[row][col].config(bg='black')
            messagebox.showinfo("Result", "Verfehlt!")

    def mark_hit_on_ship(self, hit_info):
        row, col = map(int, hit_info.split(","))
        self.buttons[row][col].config(bg='red')

if __name__ == "__main__":
    client = BattleshipClient()
