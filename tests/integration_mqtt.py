"""Optional real-broker smoke test; run with a broker already listening."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from dashboard import DashboardState, start_mqtt
from mqtt_config import MQTTConfig
from mqtt_publisher import StationPublisher
from station_events import StationSession


def wait_for(predicate, label, seconds=10):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise RuntimeError(f"Timeout aguardando {label}")


def main():
    config = MQTTConfig()
    state = DashboardState()
    dashboard = start_mqtt(config, state)
    station = StationPublisher(config)
    session = StationSession(config.station_id, station.publish)
    session.publish("status", session.status())
    station.start()
    try:
        wait_for(lambda: state.broker_connected and station.connected, "conexoes MQTT")
        wait_for(lambda: state.snapshot()["stations"].get(config.station_id, {}).get("status") == "LIVRE", "status inicial")
        student = {"id": 999, "nome": "Teste de integracao", "exercicio": "Rosca Biceps", "repeticoes": 2}
        session.login(student)
        wait_for(lambda: state.snapshot()["stations"][config.station_id]["status"] == "OCUPADA", "ocupacao")
        session.complete_series(2)
        wait_for(lambda: len(state.snapshot()["history"]) == 1, "performance")
        session.logout()
        wait_for(lambda: state.snapshot()["stations"][config.station_id]["status"] == "LIVRE", "logout")
        print("PASS: broker real, estado inicial, ocupacao, performance e logout")
    finally:
        session.logout()
        station.stop()
        dashboard.disconnect()
        dashboard.loop_stop()


if __name__ == "__main__":
    main()
