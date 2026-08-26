"""Linux half of the TCP relay; counterpart of EthernetRelay (sketch)."""

import socket
from threading import Lock, Thread
from typing import Optional

from Logger461 import logger

from app.core.config import Settings


class BridgeRelay:
    """Byte pump between the sketch's network clients and FastAPI.

    Attributes:
        _settings (Settings): Application settings for network config.
        _sockets (dict[int, socket.socket]): Active sockets keyed by slot.
        _client_ips (dict[int, str]): Client IP addresses keyed by slot.
        _map_lock (Lock): Mutex protecting socket and IP mappings.
        _bridge_lock (Lock): Mutex serializing calls across Bridge RPC.
        _bridge (Optional[object]): Arduino Bridge module or None.
        connections_total (int): Total lifetime accepted connection count.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sockets: dict[int, socket.socket] = {}
        self._client_ips: dict[int, str] = {}
        self._map_lock = Lock()
        self._bridge_lock = Lock()
        self._bridge: Optional[object] = None
        self.connections_total = 0

    def register(self) -> None:
        """Registers all Bridge callbacks."""
        try:
            from arduino.app_utils import Bridge
        except ImportError:
            logger.warning(
                "Bridge unavailable - relay not registered (dev computer)",
                metadata={"event": "relay.register.skipped"})
            return
        self._bridge = Bridge
        Bridge.provide("net_open", self._on_open)
        Bridge.provide("net_rx", self._on_rx)
        Bridge.provide("net_close", self._on_close)

    def _on_open(self, slot: int, client_ip: str) -> None:
        """Handles a new network client reported by the sketch.

        Args:
            slot (int): Connection slot assigned by the sketch.
            client_ip (str): Remote IP address seen by shield.
        """
        self._drop(slot, tell_mcu=False)
        try:
            sock = socket.create_connection(
                (self._settings.api_host, self._settings.api_port), timeout=5)
            sock.settimeout(None)
        except OSError as exc:
            logger.error("FastAPI unreachable for client",
                         metadata={"event": "relay.connect.failed",
                                   "client_ip": client_ip,
                                   "error": str(exc)},
                         extra={"slot": slot})
            self._drop(slot, tell_mcu=True)
            return
        with self._map_lock:
            self._sockets[slot] = sock
            self._client_ips[slot] = client_ip
            self.connections_total += 1
        Thread(target=self._pump_replies, args=(slot, sock),
               daemon=True).start()
        logger.debug("client connected",
                     metadata={"event": "relay.conn.open",
                               "client_ip": client_ip},
                     extra={"slot": slot})

    def _on_rx(self, slot: int, data: bytes) -> None:
        """Forwards client bytes to FastAPI.

        Args:
            slot (int): Connection slot identifier.
            data (bytes): Raw payload bytes from network client.
        """
        with self._map_lock:
            sock = self._sockets.get(slot)
        if sock is None:
            return
        try:
            sock.sendall(data)
        except OSError:
            self._drop(slot, tell_mcu=True)

    def _on_close(self, slot: int) -> None:
        """Handles the network client disconnecting.

        Args:
            slot (int): Connection slot identifier.
        """
        with self._map_lock:
            client_ip = self._client_ips.get(slot, "?")
        logger.debug("client disconnected",
                     metadata={"event": "relay.conn.close",
                               "client_ip": client_ip},
                     extra={"slot": slot})
        self._drop(slot, tell_mcu=False)

    def _pump_replies(self, slot: int, sock: socket.socket) -> None:
        """Streams FastAPI reply bytes back down to the sketch.

        Args:
            slot (int): Connection slot identifier.
            sock (socket.socket): Local socket connected to FastAPI.
        """
        try:
            data = sock.recv(self._settings.relay_chunk_bytes)
            while len(data) > 0:
                with self._bridge_lock:
                    self._bridge.call("net_tx", slot, data)
                data = sock.recv(self._settings.relay_chunk_bytes)
        except OSError:
            pass
        finally:
            self._drop(slot, tell_mcu=True)

    def _drop(self, slot: int, tell_mcu: bool) -> None:
        """Closes and forgets one mirrored connection.

        Args:
            slot (int): Connection slot identifier.
            tell_mcu (bool): True to request MCU close remote client.
        """
        with self._map_lock:
            sock = self._sockets.pop(slot, None)
            self._client_ips.pop(slot, None)
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        if (tell_mcu is True) and (self._bridge is not None):
            try:
                with self._bridge_lock:
                    self._bridge.call("net_shutdown", slot)
            except Exception:
                pass
