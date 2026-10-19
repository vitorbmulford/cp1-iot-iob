"""Shared MQTT settings from environment variables."""
import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MQTTConfig:
    host: str = os.getenv("SMARTGYM_MQTT_HOST", "localhost")
    port: int = int(os.getenv("SMARTGYM_MQTT_PORT", "1883"))
    username: str | None = os.getenv("SMARTGYM_MQTT_USERNAME") or None
    password: str | None = os.getenv("SMARTGYM_MQTT_PASSWORD") or None
    prefix: str = os.getenv("SMARTGYM_MQTT_PREFIX", "smartgym").strip("/")
    station_id: str = os.getenv("SMARTGYM_STATION_ID", "estacao01")

    def __post_init__(self):
        if not self.host or not 1 <= self.port <= 65535:
            raise ValueError("Host ou porta MQTT invalidos")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", self.station_id):
            raise ValueError("SMARTGYM_STATION_ID invalido")
        if not self.prefix or any(not p or any(c in p for c in "+#") for p in self.prefix.split("/")):
            raise ValueError("SMARTGYM_MQTT_PREFIX invalido")

    def topic(self, station_id, event):
        return f"{self.prefix}/stations/{station_id}/{event}"

    def subscription(self):
        return f"{self.prefix}/stations/+/+"
