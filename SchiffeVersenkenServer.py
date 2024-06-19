import socket
import threading
 
class BattleshipServer:
    def __init__(self, host='192.168.5.179', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(2)
        print("Server started, waiting for players to connect...")
 
        self.clients = []
        self.lock = threading.Lock()
        self.ship_positions_player_1 = None
        self.ship_positions_player_2 = None
        self.current_turn = 0  # 0 for player 1, 1 for player 2
 
    def handle_client(self, client, player_id):
        colors = ['red', 'blue']
        client.sendall(f"PLAYER_ID:{player_id}".encode())  # Send player ID first
        client.sendall(f"COLOR:{colors[player_id-1]}".encode())
        client.sendall(f"WELCOME:Welcome Player {player_id}".encode())
 
        while True:
            try:
                msg = client.recv(1024).decode()
                if msg.startswith("SHIP_POSITIONS:"):
                    positions = msg[len("SHIP_POSITIONS:"):]
                    if player_id == 1:
                        self.ship_positions_player_1 = positions
                        print(f"Received ship positions from Player 1: {self.ship_positions_player_1}")
                    elif player_id == 2:
                        self.ship_positions_player_2 = positions
                        print(f"Received ship positions from Player 2: {self.ship_positions_player_2}")
 
                    self.print_boards()  # Print boards for debugging
 
                    if self.ship_positions_player_1 and self.ship_positions_player_2:
                        self.send_opponent_positions()
                        self.start_game()
                elif msg.startswith("GUESS:"):
                    guess = msg[len("GUESS:"):].split(":")
                    row, col = int(guess[0]), int(guess[1])
                    self.process_guess(player_id, row, col)
                else:
                    self.broadcast(msg, client)
            except Exception as e:
                print(f"Error: {e}")
                break
 
        with self.lock:
            self.clients.remove(client)
        client.close()
 
    def broadcast(self, msg, sender_client):
        with self.lock:
            for client in self.clients:
                if client != sender_client:
                    client.sendall(msg.encode())
 
    def send_opponent_positions(self):
        self.clients[0].sendall(f"OPPONENT_SHIP_POSITIONS:{self.ship_positions_player_2}".encode())
        self.clients[1].sendall(f"OPPONENT_SHIP_POSITIONS:{self.ship_positions_player_1}".encode())
        print(f"Sent Player 1's positions to Player 2: {self.ship_positions_player_1}")
        print(f"Sent Player 2's positions to Player 1: {self.ship_positions_player_2}")
 
    def start_game(self):
        self.clients[0].sendall("TURN:YES".encode())  # Player 1 starts
        self.clients[1].sendall("TURN:NO".encode())
 
    def process_guess(self, player_id, row, col):
        opponent_id = 2 if player_id == 1 else 1
        opponent_positions = self.ship_positions_player_2 if player_id == 1 else self.ship_positions_player_1
        guess_result = "HIT" if f"{row}:{col}" in opponent_positions else "MISS"
 
        self.clients[player_id-1].sendall(f"RESULT:{row},{col},{guess_result}".encode())
        self.clients[opponent_id-1].sendall(f"RESULT:{row},{col},{guess_result}".encode())
 
        if guess_result == "MISS":
            # Switch turn only if the guess was a miss
            self.current_turn = 1 if self.current_turn == 0 else 0
 
        self.clients[self.current_turn].sendall("TURN:YES".encode())
        self.clients[1 - self.current_turn].sendall("TURN:NO".encode())
 
    def print_boards(self):
        if self.ship_positions_player_1:
            print("Player 1's Board:")
            print(self.ship_positions_player_1)
        if self.ship_positions_player_2:
            print("Player 2's Board:")
            print(self.ship_positions_player_2)
 
    def start(self):
        player_id = 1
        while len(self.clients) < 2:
            client, addr = self.server.accept()
            self.clients.append(client)
            threading.Thread(target=self.handle_client, args=(client, player_id)).start()
            print(f"Player {player_id} connected from {addr}")
            player_id += 1
 
if __name__ == "__main__":
    server = BattleshipServer()
    server.start()
 