from __future__ import annotations

import json
import socket
import struct

from .model import ListenerFrame


def _osc_string(value: str) -> bytes:
    data = value.encode("utf-8") + b"\0"
    return data + b"\0" * ((4 - len(data) % 4) % 4)


def osc_message(address: str, values: list[float | int | str]) -> bytes:
    tags, payload = ",", bytearray()
    for value in values:
        if isinstance(value, str):
            tags += "s"; payload.extend(_osc_string(value))
        elif isinstance(value, int):
            tags += "i"; payload.extend(struct.pack(">i", value))
        else:
            tags += "f"; payload.extend(struct.pack(">f", float(value)))
    return _osc_string(address) + _osc_string(tags) + bytes(payload)


class ListenerOutput:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000, osc: bool = True, ndjson: bool = True):
        self.address, self.osc, self.ndjson = (host, port), osc, ndjson
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if osc else None

    def send(self, frame: ListenerFrame) -> None:
        if self.ndjson:
            print(json.dumps(frame.to_dict(), separators=(",", ":")), flush=True)
        if not self.socket:
            return
        self.socket.sendto(osc_message("/mirror/rms", [frame.features.rms]), self.address)
        self.socket.sendto(osc_message("/mirror/centroid", [frame.features.centroid_hz]), self.address)
        for name, quality in frame.state.items():
            self.socket.sendto(osc_message("/mirror/listener/v1/quality", [name, quality.value, quality.trend, quality.confidence]), self.address)
        for event in frame.events:
            if "quality" in event:
                values = [event["quality"], event["verb"], event["strength"], event["confidence"]]
                self.socket.sendto(osc_message("/mirror/listener/v1/event", values), self.address)
            elif event.get("type") == "recurrence":
                values = [event["passage_id"], event["similarity"], event["confidence"]]
                self.socket.sendto(osc_message("/mirror/listener/v1/recurrence", values), self.address)
            elif event.get("type") == "passage":
                values = [event["passage_id"], event["confidence"]]
                self.socket.sendto(osc_message("/mirror/listener/v1/passage", values), self.address)
        for domain, image in frame.synesthesia.items():
            self.socket.sendto(osc_message("/mirror/listener/v1/synesthesia",
                                          [domain, image["primary"], image["confidence"]]), self.address)
        image = frame.numeric_image
        self.socket.sendto(osc_message("/mirror/listener/v1/numeric_image", [image.value, image.confidence, image.descriptor]), self.address)

    def close(self) -> None:
        if self.socket:
            self.socket.close()
