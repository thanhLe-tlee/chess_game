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
        self.rematch_requests: Dict[str, bool] = {}
        self.game_active = False

    def assign_slot(self, conn: socket.socket) -> Optional[str]:
        with self.lock:
            for color in ("white", "black"):
                if color not in self.players:
                    if not self.players:
                        self.state = chessEngine.GameState()
                    self.players[color] = conn
                    if len(self.players) == 2:
                        self.game_active = True
                    return color
        return None

    def release_slot(self, color: str) -> None:
        with self.lock:
            self.players.pop(color, None)
            if not self.players:
                self.state = chessEngine.GameState()
                self.game_active = False
                self.rematch_requests.clear()

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
                self.rematch_requests.clear()
                self.state = chessEngine.GameState()
                self.game_active = True
                return "rematch_accepted"
            else:
                return "waiting_for_opponent"
    
    def cancel_rematch(self, color: str) -> None:
        """Cancel rematch request"""
        with self.lock:
            self.rematch_requests.pop(color, None)
    
    def check_rematch_status(self) -> str:
        """Check if rematch has been accepted by both players"""
        with self.lock:
            if len(self.rematch_requests) == 2 and all(self.rematch_requests.values()):
                self.rematch_requests.clear()
                self.state = chessEngine.GameState()
                self.game_active = True
                return "rematch_accepted"
            elif len(self.rematch_requests) == 1:
                return "waiting_for_opponent"
            else:
                return "no_rematch"
    
    def both_players_ready(self) -> bool:
        """Check if both players are connected"""
        with self.lock:
            return len(self.players) == 2


session = GameSession()
matchmaking_queue = []
matchmaking_lock = threading.Lock()


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
    server.listen(10)
    print(f"Chess server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print(f"New connection from {addr}")
        
        # Add to matchmaking queue
        with matchmaking_lock:
            matchmaking_queue.append(conn)
            print(f"Player added to queue. Queue size: {len(matchmaking_queue)}")
            
            # Try to match two players
            if len(matchmaking_queue) >= 2:
                player1_conn = matchmaking_queue.pop(0)
                player2_conn = matchmaking_queue.pop(0)
                
                # Assign colors
                color1 = session.assign_slot(player1_conn)
                color2 = session.assign_slot(player2_conn)
                
                if color1 and color2:
                    print(f"Matched two players: {color1} and {color2}")
                    threading.Thread(target=handle_client, args=(player1_conn, addr, color1), daemon=True).start()
                    threading.Thread(target=handle_client, args=(player2_conn, addr, color2), daemon=True).start()
                else:
                    # Something went wrong, close connections
                    try:
                        player1_conn.close()
                        player2_conn.close()
                    except:
                        pass


if __name__ == "__main__":
    main()
