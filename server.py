import socket
import threading

clients = []

def handle_client(conn, addr):
    print(f"Player connected: {addr}")
    clients.append(conn)

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            # broadcast move to the other player
            for c in clients:
                if c != conn:
                    c.send(data)
        except:
            break

    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 5000))
server.listen(2)

print("Server ready... waiting for 2 players")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()
