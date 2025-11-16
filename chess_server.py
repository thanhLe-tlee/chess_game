import socket
import pickle
import threading
import chess_engine


class ChessServer:
    """
    Chess server that manages multiple games and clients.
    Handles matchmaking and game state synchronization.
    """
    
    def __init__(self, host="0.0.0.0", port=5555):
        """
        Initialize the chess server
        Args:
            host: Server IP address (0.0.0.0 binds to all interfaces for internet access)
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # List to hold all active games
        self.games = []
        
        # Dictionary to track which client belongs to which game
        # Format: {connection: (game_id, player_color)}
        self.connections = {}
        
        # Lock for thread-safe operations
        self.lock = threading.Lock()
        
        # Waiting clients who need a match
        self.waiting_client = None
        
    def start(self):
        """Start the server and begin accepting connections"""
        try:
            self.server.bind((self.host, self.port))
        except socket.error as e:
            print(f"Error binding server: {e}")
            return
        
        self.server.listen()
        print(f"Chess Server started on {self.host}:{self.port}")
        print("Waiting for connections...")
        
        while True:
            try:
                conn, addr = self.server.accept()
                print(f"New connection from: {addr}")
                
                # Start a new thread to handle this client
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
                
            except Exception as e:
                print(f"Error accepting connection: {e}")
    
    def handle_client(self, conn, addr):
        """Handle a connected client"""
        try:
            with self.lock:
                if self.waiting_client is None:
                    # This is the first player - create a new game
                    game = chess_engine.GameState()
                    game_id = len(self.games)
                    self.games.append(game)
                    
                    # Assign this player as white
                    self.connections[conn] = (game_id, "white")
                    self.waiting_client = conn
                    
                    # Send color to client
                    conn.send("white".encode())
                    print(f"{addr} joined game {game_id} as WHITE")
                    
                else:
                    # This is the second player - match with waiting player
                    waiting_conn = self.waiting_client
                    game_id = self.connections[waiting_conn][0]
                    
                    # Assign this player as black
                    self.connections[conn] = (game_id, "black")
                    self.waiting_client = None
                    
                    # Send color to client
                    conn.send("black".encode())
                    print(f"{addr} joined game {game_id} as BLACK")
                    print(f"Game {game_id} is now ready to start!")
            
            # Handle client requests
            while True:
                try:
                    data = pickle.loads(conn.recv(4096 * 4))
                    
                    with self.lock:
                        game_id, player_color = self.connections[conn]
                        game = self.games[game_id]
                        
                        if data == "get":
                            # Client wants to get the current game state
                            response = game
                        elif isinstance(data, chess_engine.GameState):
                            # Client sent an updated game state (made a move)
                            self.games[game_id] = data
                            response = data
                            print(f"Game {game_id}: {player_color} made a move")
                        else:
                            response = game
                    
                    # Send response back to client
                    conn.send(pickle.dumps(response))
                    
                except EOFError:
                    # Client disconnected
                    break
                except Exception as e:
                    print(f"Error handling client {addr}: {e}")
                    break
            
        except Exception as e:
            print(f"Error in client handler for {addr}: {e}")
        
        finally:
            # Clean up when client disconnects
            with self.lock:
                if conn in self.connections:
                    game_id, player_color = self.connections[conn]
                    print(f"{addr} disconnected from game {game_id} ({player_color})")
                    
                    # If this was the waiting client, reset it
                    if conn == self.waiting_client:
                        self.waiting_client = None
                    
                    del self.connections[conn]
            
            conn.close()


def main():
    """Main function to start the server"""
    print("=" * 50)
    print("Chess Server for Online Multiplayer")
    print("=" * 50)
    
    # For internet play:
    # 1. Set host to "0.0.0.0" to accept connections from any IP
    # 2. Port forward port 5555 on your router to this computer
    # 3. Give your public IP address to clients
    # 4. Make sure firewall allows connections on port 5555
    
    server = ChessServer(host="0.0.0.0", port=5555)
    server.start()


if __name__ == "__main__":
    main()
