"""Client-side networking helpers for online chess play."""
from __future__ import annotations

import os
import pickle
import socket
import struct
from typing import Any, Optional

_DEFAULT_HOST = os.getenv("CHESS_SERVER_HOST", "127.0.0.1")
_DEFAULT_PORT = int(os.getenv("CHESS_SERVER_PORT", "5000"))
_HEADER_STRUCT = struct.Struct("!I")  # 4-byte unsigned int length prefix


class NetworkError(RuntimeError):
    """Raised when a network operation fails."""


class Network:
    """Simple synchronous client used by the Pygame UI."""

    def __init__(self, host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT, timeout: float = 10.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None

    def connect(self) -> str:
        """Connect to the chess server and return the assigned player color."""
        if self._socket:
            return self._await_payload()

        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            sock.settimeout(self.timeout)
            self._socket = sock
            color = self._await_payload()
            if color == "server_full":
                raise NetworkError("Server already has two active players")
            if not isinstance(color, str):
                raise NetworkError("Unexpected handshake payload from server")
            return color
        except OSError as exc:
            raise NetworkError(f"Unable to connect to chess server at {self.host}:{self.port}") from exc

    def send(self, data: Any) -> Any:
        """Send arbitrary picklable data and wait for the server response."""
        if not self._socket:
            raise NetworkError("Not connected to server")
        try:
            self._send_payload(data)
            return self._await_payload()
        except OSError as exc:
            self.close()
            raise NetworkError("Lost connection to server") from exc

    def close(self) -> None:
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _send_payload(self, data: Any) -> None:
        payload = pickle.dumps(data)
        header = _HEADER_STRUCT.pack(len(payload))
        assert self._socket is not None
        self._socket.sendall(header + payload)

    def _await_payload(self) -> Any:
        assert self._socket is not None
        raw_header = self._recv_exact(_HEADER_STRUCT.size)
        (length,) = _HEADER_STRUCT.unpack(raw_header)
        raw_payload = self._recv_exact(length)
        return pickle.loads(raw_payload)

    def _recv_exact(self, size: int) -> bytes:
        assert self._socket is not None
        data = bytearray()
        while len(data) < size:
            chunk = self._socket.recv(size - len(data))
            if not chunk:
                raise NetworkError("Connection closed by server")
            data.extend(chunk)
        return bytes(data)
