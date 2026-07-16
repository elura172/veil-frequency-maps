from __future__ import annotations

import socket
import struct

from .model import MirrorState, QUALITIES


def _string(value: str) -> bytes:
    data = value.encode("utf-8") + b"\0"
    return data + b"\0" * ((4 - len(data) % 4) % 4)


def encode_message(address: str, values: list[float | int | str]) -> bytes:
    tags, payload = ",", bytearray()
    for value in values:
        if isinstance(value, str): tags += "s"; payload.extend(_string(value))
        elif isinstance(value, int): tags += "i"; payload.extend(struct.pack(">i", value))
        else: tags += "f"; payload.extend(struct.pack(">f", float(value)))
    return _string(address) + _string(tags) + bytes(payload)


class MirrorOSCSender:
    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        self.address = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, state: MirrorState) -> None:
        for quality in QUALITIES:
            self.socket.sendto(encode_message("/mirror/voice/" + quality, [state.values[quality]]), self.address)
        self.socket.sendto(encode_message("/mirror/voice/state", [state.values[key] for key in QUALITIES]), self.address)
        self.socket.sendto(encode_message("/mirror/voice/silence", [state.silence_presence]), self.address)

    def close(self) -> None:
        self.socket.close()
