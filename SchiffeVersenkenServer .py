import socket
import threading

class BattleshipServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print("Server started, waiting for players to connect...")

        self.clients = []
        self.lock = threading.Lock()
        self.ship_positions = [None, None]
        self.hits = [[], []]  # To track hits for each player
        self.current_turn = 0  # 0 for player 1, 1 for player 2

    def handle_client(self, client, player_id):
        colors = ['blue', 'green']
        client.sendall(f"PLAYER_ID:{player_id}\n".encode())
        client.sendall(f"COLOR:{colors[player_id]}\n".encode())
        client.sendall(f"WELCOME:Welcome Player {player_id+1}\n".encode())

        while True:
            try:
                msg = client.recv(1024).decode().strip()
                if msg.startswith("SHIP_POSITIONS:"):
                    positions = msg[len("SHIP_POSITIONS:"):]
                    self.ship_positions[player_id] = positions
                    print(f"Received ship positions from Player {player_id+1}: {positions}")

                    if all(self.ship_positions):
                        self.send_opponent_positions()
                        self.start_game()
                elif msg.startswith("GUESS:"):
                    guess = msg[len("GUESS:"):].split(":")
                    row, col = int(guess[0]), int(guess[1])
                    self.process_guess(player_id, row, col)
            except Exception as e:
                print(f"Error: {e}")
                break

        with self.lock:
            self.clients.remove(client)
        client.close()

    def send_opponent_positions(self):
        self.clients[0].sendall(f"OPPONENT_SHIP_POSITIONS:{self.ship_positions[1]}\n".encode())
        self.clients[1].sendall(f"OPPONENT_SHIP_POSITIONS:{self.ship_positions[0]}\n".encode())
        print("Sent opponent ship positions to both players.")

    def start_game(self):
        self.clients[0].sendall("TURN:YES\n".encode())
        self.clients[1].sendall("TURN:NO\n".encode())

    def process_guess(self, player_id, row, col):
        opponent_id = 1 if player_id == 0 else 0
        opponent_positions = self.ship_positions[opponent_id].split(',')
        guess_result = "HIT" if f"{row}:{col}" in opponent_positions else "MISS"

        # Send the result to the player who made the guess
        self.clients[player_id].sendall(f"RESULT:{row},{col},{guess_result}\n".encode())

        # Notify the opponent if their ship was hit or missed
        if guess_result == "HIT":
            self.clients[opponent_id].sendall(f"HIT_ON_SHIP:{row},{col}\n".encode())
            self.hits[player_id].append(f"{row}:{col}")
            if self.check_win(player_id, opponent_positions):
                self.clients[player_id].sendall("WIN:YES\n".encode())
                self.clients[opponent_id].sendall("WIN:NO\n".encode())
                return  # End the game after a win
        else:
            self.clients[opponent_id].sendall(f"MISS_ON_SHIP:{row},{col}\n".encode())

        if guess_result == "MISS":
            self.current_turn = opponent_id

        self.clients[self.current_turn].sendall("TURN:YES\n".encode())
        self.clients[1 - self.current_turn].sendall("TURN:NO\n".encode())

    def check_win(self, player_id, opponent_positions):
        # Check if all ships of the opponent are hit
        return all(pos in self.hits[player_id] for pos in opponent_positions)

    def start(self):
        player_id = 0
        while len(self.clients) < 2:
            client, addr = self.server.accept()
            self.clients.append(client)
            threading.Thread(target=self.handle_client, args=(client, player_id)).start()
            print(f"Player {player_id+1} connected from {addr}")
            player_id += 1

if __name__ == "__main__":
    server = BattleshipServer()
    server.start()
