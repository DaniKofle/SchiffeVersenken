import socket
import pickle
import threading

class GameServer:
    def __init__(self, host='10.10.218.24', port=8080):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(2)
        self.connections = []
        self.boards = [None, None]
        self.ships = [None, None]
        self.current_player = 0
        self.hits = [0, 0]

    def start(self):
        print("Server started, waiting for connections...")
        while len(self.connections) < 2:
            conn, addr = self.server.accept()
            print(f"Connected to: {addr}")
            self.connections.append(conn)
            threading.Thread(target=self.handle_client, args=(conn, len(self.connections)-1)).start()

        print("Both players connected. Waiting for ship placement...")

    def send_all(self, message, data=None):
        for conn in self.connections:
            try:
                conn.send(pickle.dumps((message, data)))
            except:
                print(f"Error sending message to player {self.connections.index(conn)+1}")
                conn.close()
                self.connections.remove(conn)

    def send_to_player(self, player, message, data=None):
        try:
            self.connections[player].send(pickle.dumps((message, data)))
        except:
            print(f"Error sending message to player {player+1}")
            self.connections[player].close()
            self.connections.remove(self.connections[player])

    def handle_client(self, conn, player):
        while True:
            try:
                data = pickle.loads(conn.recv(4096))
                if data:
                    self.handle_message(player, data)
            except:
                print(f"Player {player+1} disconnected")
                self.connections.remove(conn)
                break

    def handle_message(self, player, message):
        command, data = message
        if command == "place_ship":
            self.boards[player], self.ships[player] = data
            print(f"Player {player+1} has placed their ships.")
            if all(self.boards):
                self.send_boards()
                self.send_all("both_boards_placed")
                self.send_all("player_turn", self.current_player)
        elif command == "guess":
            x, y = data
            opponent = 1 if player == 0 else 0
            board = self.boards[opponent]
            result = "miss"
            if board[x][y] == "S":
                result = "hit"
                board[x][y] = "H"
                self.hits[player] += 1
                ship_name = self.check_sunk_ship(x, y, self.ships[opponent])
                if ship_name:
                    result = f"sunk {ship_name}"
                if self.check_win(self.hits[player]):
                    self.send_all("win", player)
                    return
            else:
                board[x][y] = "M"
                self.current_player = opponent

            self.send_to_player(player, "guess_result", (player, x, y, result))
            self.send_to_player(opponent, "guess_result", (player, x, y, result))
            if result == "miss":
                self.send_all("player_turn", self.current_player)
            else:
                self.send_to_player(player, "player_turn", player)

    def send_boards(self):
        for i, conn in enumerate(self.connections):
            opponent_board = self.boards[1 - i]
            conn.send(pickle.dumps(("set_guess_board", opponent_board)))

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
    server = GameServer()
    server.start()
