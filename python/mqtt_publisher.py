"""Nonblocking MQTT publisher with retained state and reconnect buffering."""
import json
import logging
import threading
from collections import deque

import paho.mqtt.client as mqtt

LOG = logging.getLogger(__name__)


class StationPublisher:
    def __init__(self, config):
        self.config = config
        self.lock = threading.RLock()
        self.connected = False
        self.current_status = None
        self.pending = deque(maxlen=200)
        self.last_info = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                  client_id=f"smartgym-station-{config.station_id}")
        if config.username:
            self.client.username_pw_set(config.username, config.password)
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def start(self):
        self.client.connect_async(self.config.host, self.config.port, keepalive=30)
        self.client.loop_start()

    def _send(self, event, payload):
        info = self.client.publish(self.config.topic(self.config.station_id, event),
                                   json.dumps(payload, ensure_ascii=False), qos=1,
                                   retain=(event == "status"))
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            LOG.warning("Falha ao publicar %s: %s", event, info.rc)
            return False
        self.last_info = info
        return True

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        with self.lock:
            self.connected = not reason_code.is_failure
            if not self.connected:
                LOG.error("Broker recusou a estacao: %s", reason_code)
                return
            LOG.info("Estacao conectada ao broker")
            self.client.subscribe(f"{self.config.prefix}/dashboard/sync/ready", qos=1)
            if self.current_status:
                self._send("status", self.current_status)
            # Send to broker now; replay on dashboard readiness if it was late.
            for event, payload in self.pending:
                self._send(event, payload)
            self.client.publish(f"{self.config.prefix}/dashboard/sync/request",
                                self.config.station_id, qos=1)

    def _on_message(self, client, userdata, message):
        if message.topic != f"{self.config.prefix}/dashboard/sync/ready":
            return
        with self.lock:
            while self.pending:
                event, payload = self.pending[0]
                if not self._send(event, payload):
                    break
                self.pending.popleft()

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        with self.lock:
            self.connected = False
        LOG.warning("Estacao desconectada do broker: %s", reason_code)

    def publish(self, event, payload):
        with self.lock:
            if event == "status":
                self.current_status = payload
            if self.connected and self._send(event, payload):
                return
            if event == "performance":
                if len(self.pending) == self.pending.maxlen:
                    LOG.error("Fila MQTT cheia; performance antiga descartada")
                self.pending.append((event, payload))
            else:
                LOG.warning("Status sincronizado apos reconexao MQTT")

    def stop(self):
        # Give the last QoS 1 message (often logout) time to reach the broker.
        if self.connected and self.last_info is not None:
            try:
                self.last_info.wait_for_publish(timeout=2)
            except (RuntimeError, ValueError):
                LOG.warning("Ultima mensagem MQTT nao foi confirmada antes do encerramento")
        self.client.disconnect()
        self.client.loop_stop()
