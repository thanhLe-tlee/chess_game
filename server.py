"""Simple TCP relay server for multiplayer chess."""

from __future__ import annotations

import os
import pickle
import socket
import struct
import threading
from typing import Dict, Optional

import chess_engine as chessEngine

HOST = os.getenv("CHESS_SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("CHESS_SERVER_PORT", "5000"))
HEADER = struct.Struct("!I")


def send_payload(conn: socket.socket, payload) -> None:
    data = pickle.dumps(payload)
    conn.sendall(HEADER.pack(len(data)) + data)


def recv_payload(conn: socket.socket):
    header = _recv_exact(conn, HEADER.size)
    (length,) = HEADER.unpack(header)
    body = _recv_exact(conn, length)
    return pickle.loads(body)


def _recv_exact(conn: socket.socket, size: int) -> bytes:
    buf = bytearray()
    while len(buf) < size:
        chunk = conn.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("Client disconnected")
        buf.extend(chunk)
    return bytes(buf)


class GameSession:
    """Keeps the current game state and active connections."""

    def __init__(self) -> None:
        self.state = chessEngine.GameState()
        self.lock = threading.Lock()
        self.players: Dict[str, socket.socket] = {}

    def assign_slot(self, conn: socket.socket) -> Optional[str]:
        with self.lock:
            for color in ("white", "black"):
                if color not in self.players:
                    if not self.players:
                        self.state = chessEngine.GameState()
                    self.players[color] = conn
                    return color
        return None

    def release_slot(self, color: str) -> None:
        with self.lock:
            self.players.pop(color, None)
            if not self.players:
                self.state = chessEngine.GameState()

    def get_state(self):
        with self.lock:
            return self.state

    def update_state(self, state):
        with self.lock:
            self.state = state


session = GameSession()


def handle_client(conn: socket.socket, addr, color: str) -> None:
    print(f"{color.title()} player connected from {addr}")
    try:
        send_payload(conn, color)
        while True:
            data = recv_payload(conn)
            if data == "get":
                send_payload(conn, session.get_state())
            elif isinstance(data, chessEngine.GameState):
                session.update_state(data)
                send_payload(conn, session.get_state())
            else:
                # Unknown payload; echo last known state so clients stay in sync
                send_payload(conn, session.get_state())
    except Exception as exc:
        print(f"Connection with {color} player lost: {exc}")
    finally:
        session.release_slot(color)
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        conn.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)
    print(f"Chess server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        color = session.assign_slot(conn)
        if color is None:
            print(f"Rejecting connection from {addr}: game in progress")
            send_payload(conn, "server_full")
            conn.close()
            continue
        threading.Thread(target=handle_client, args=(conn, addr, color), daemon=True).start()


if __name__ == "__main__":
    main()
