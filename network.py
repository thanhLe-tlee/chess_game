import socket
import pickle


class Network:
    """Client network class for connecting to the chess server"""
    
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Server address - change this to your public server IP for internet play
        # For local testing, use "127.0.0.1"
        # For internet play, use your server's public IP address
        self.server = "0.0.0.0"  # Change to server IP
        self.port = 5555
        self.addr = (self.server, self.port)
        self.color = None
        
    def connect(self):
        """Connect to server and receive assigned color"""
        try:
            self.client.connect(self.addr)
            # Receive the assigned color from server
            self.color = self.client.recv(2048).decode()
            print(f"Connected to server! Assigned color: {self.color}")
            return self.color
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return None
    
    def send(self, data):
        """Send data to server and receive response"""
        try:
            # Serialize and send data
            self.client.send(pickle.dumps(data))
            # Receive response
            response = pickle.loads(self.client.recv(4096 * 4))
            return response
        except socket.error as e:
            print(f"Socket error: {e}")
            return None
        except Exception as e:
            print(f"Error sending data: {e}")
            return None
    
    def close(self):
        """Close the connection"""
        try:
            self.client.close()
        except:
            pass
