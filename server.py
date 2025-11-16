from __future__ import annotations

import os
import pickle
import random
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
        self.rematch_requests: Dict[str, bool] = {}
        self.rematch_accepted = False

    def assign_slot(self, conn: socket.socket) -> Optional[str]:
        with self.lock:
            # If no players connected yet, randomly assign first color
            if not self.players:
                first_color = random.choice(["white", "black"])
                self.state = chessEngine.GameState()
                self.players[first_color] = conn
                return first_color
            # Second player gets the opposite color
            elif len(self.players) == 1:
                if "white" in self.players:
                    self.players["black"] = conn
                    return "black"
                else:
                    self.players["white"] = conn
                    return "white"
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
    
    def request_rematch(self, color: str) -> str:
        """Register a rematch request and return status"""
        with self.lock:
            self.rematch_requests[color] = True
            if len(self.rematch_requests) == 2 and all(self.rematch_requests.values()):
                # Both players want rematch
                self.rematch_accepted = True
                self.state = chessEngine.GameState()
                return "rematch_accepted"
            else:
                return "waiting_for_opponent"
    
    def cancel_rematch(self, color: str) -> None:
        """Cancel rematch request"""
        with self.lock:
            self.rematch_requests.pop(color, None)
            if not self.rematch_requests:
                self.rematch_accepted = False
    
    def check_rematch_status(self) -> str:
        """Check if rematch has been accepted by both players"""
        with self.lock:
            if self.rematch_accepted:
                return "rematch_accepted"
            elif len(self.rematch_requests) == 1:
                return "waiting_for_opponent"
            else:
                return "no_rematch"
    
    def both_players_ready(self) -> bool:
        """Check if both players are connected"""
        with self.lock:
            if self.rematch_accepted and len(self.players) == 2:
                # During rematch, immediately return True since players are already connected
                # Reset rematch state when both players confirm they're ready
                self.rematch_accepted = False
                self.rematch_requests.clear()
                return True
            return len(self.players) == 2


session = GameSession()


def handle_client(conn: socket.socket, addr, color: str) -> None:
    print(f"{color.title()} player connected from {addr}")
    try:
        send_payload(conn, color)
        while True:
            data = recv_payload(conn)
            if data == "get":
                send_payload(conn, session.get_state())
            elif data == "request_rematch":
                status = session.request_rematch(color)
                send_payload(conn, status)
            elif data == "check_rematch":
                status = session.check_rematch_status()
                send_payload(conn, status)
            elif data == "cancel_rematch":
                session.cancel_rematch(color)
                send_payload(conn, "rematch_cancelled")
            elif data == "check_both_ready":
                ready = session.both_players_ready()
                send_payload(conn, ready)
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
