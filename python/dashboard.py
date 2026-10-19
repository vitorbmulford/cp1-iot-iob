"""MQTT subscriber and real-time Flask/SSE management dashboard."""
import json
import logging
import os
import queue
import re
import threading
from collections import deque
from uuid import uuid4

import paho.mqtt.client as mqtt
from flask import Flask, Response, jsonify, render_template, stream_with_context

from mqtt_config import MQTTConfig

LOG = logging.getLogger(__name__)


class DashboardState:
    def __init__(self, limit=100):
        self.lock = threading.RLock()
        self.stations = {}
        self.history = deque(maxlen=limit)
        self.seen = set()
        self.listeners = set()
        self.broker_connected = False

    def snapshot(self):
        with self.lock:
            return {"broker_connected": self.broker_connected,
                    "stations": dict(self.stations), "history": list(self.history)}

    def announce(self):
        data = self.snapshot()
        with self.lock:
            for listener in list(self.listeners):
                try:
                    listener.put_nowait(data)
                except queue.Full:
                    listener.get_nowait()
                    listener.put_nowait(data)

    def set_connection(self, value):
        with self.lock:
            self.broker_connected = value
        self.announce()

    def accept(self, topic, payload, retained, config):
        match = re.fullmatch(re.escape(config.prefix) + r"/stations/([A-Za-z0-9_-]+)/(status|performance)", topic)
        if not match:
            return False
        station_id, event = match.groups()
        if event == "performance" and retained:
            return False
        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            LOG.warning("Payload MQTT invalido em %s", topic)
            return False
        if not isinstance(data, dict) or data.get("station_id") != station_id:
            return False
        if event == "status":
            if data.get("status") not in ("LIVRE", "OCUPADA"):
                return False
            if data["status"] == "OCUPADA" and not isinstance(data.get("student_name"), str):
                return False
            with self.lock:
                self.stations[station_id] = data
        else:
            if (not isinstance(data.get("event_id"), str) or
                not isinstance(data.get("student_name"), str) or
                type(data.get("repetitions")) is not int or data["repetitions"] < 0 or
                not isinstance(data.get("timestamp"), str) or
                not isinstance(data.get("series_id"), str)):
                return False
            with self.lock:
                if data["event_id"] in self.seen:
                    return False
                self.seen.add(data["event_id"])
                if len(self.seen) > 2000:
                    self.seen = {row["event_id"] for row in self.history}
                self.history.appendleft(data)
        self.announce()
        return True


def create_app(state=None):
    app = Flask(__name__)
    state = state or DashboardState()
    app.config["DASHBOARD_STATE"] = state

    @app.get("/")
    def index():
        return render_template("dashboard.html")

    @app.get("/api/state")
    def current_state():
        return jsonify(state.snapshot())

    @app.get("/events")
    def events():
        listener = queue.Queue(maxsize=2)
        with state.lock:
            state.listeners.add(listener)
        def generate():
            try:
                yield f"data: {json.dumps(state.snapshot(), ensure_ascii=False)}\n\n"
                while True:
                    try:
                        data = listener.get(timeout=20)
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    except queue.Empty:
                        yield ": heartbeat\n\n"
            finally:
                with state.lock:
                    state.listeners.discard(listener)
        return Response(stream_with_context(generate()), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return app


def start_mqtt(config, state):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"smartgym-dashboard-{uuid4().hex[:8]}")
    if config.username:
        client.username_pw_set(config.username, config.password)
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            LOG.error("Broker recusou dashboard: %s", reason_code)
            state.set_connection(False)
            return
        client.subscribe(config.subscription(), qos=1)
        client.subscribe(f"{config.prefix}/dashboard/sync/request", qos=1)
        state.set_connection(True)
        client.publish(f"{config.prefix}/dashboard/sync/ready", "ready", qos=1)
        LOG.info("Dashboard assinou %s", config.subscription())

    def on_disconnect(client, userdata, flags, reason_code, properties):
        state.set_connection(False)
        LOG.warning("Dashboard desconectado do broker: %s", reason_code)

    def on_message(client, userdata, message):
        if message.topic == f"{config.prefix}/dashboard/sync/request":
            client.publish(f"{config.prefix}/dashboard/sync/ready", "ready", qos=1)
            return
        state.accept(message.topic, message.payload, message.retain, config)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect_async(config.host, config.port, keepalive=30)
    client.loop_start()
    return client


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = MQTTConfig()
    state = DashboardState()
    client = start_mqtt(config, state)
    try:
        create_app(state).run(host=os.getenv("SMARTGYM_DASHBOARD_HOST", "127.0.0.1"),
                              port=int(os.getenv("SMARTGYM_DASHBOARD_PORT", "5000")),
                              debug=False, use_reloader=False, threaded=True)
    finally:
        client.disconnect()
        client.loop_stop()
