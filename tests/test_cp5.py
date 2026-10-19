import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
import database
import serial
import serial_io
from dashboard import DashboardState, create_app
from exercise_counter import BicepCurlCounter
from mqtt_config import MQTTConfig
from station_events import StationSession


class CP5Tests(unittest.TestCase):
    def setUp(self):
        self.config = MQTTConfig(host="localhost", station_id="estacao01")
        self.state = DashboardState()
        self.events = []
        self.session = StationSession("estacao01", lambda kind, payload: self.events.append((kind, payload)))
        self.student = {"id": 7, "nome": "Aluno teste", "exercicio": "Rosca Biceps", "repeticoes": 1}

    def deliver(self):
        for kind, payload in self.events:
            self.state.accept(self.config.topic("estacao01", kind), json.dumps(payload).encode(), False, self.config)
        self.events.clear()

    def test_full_session(self):
        self.assertFalse(self.session.login(None))
        self.assertEqual(self.events, [])
        self.assertTrue(self.session.login(self.student))
        self.deliver()
        self.assertEqual(self.state.snapshot()["stations"]["estacao01"]["status"], "OCUPADA")
        self.assertFalse(self.session.complete_series(0))
        self.assertTrue(self.session.complete_series(1))
        self.assertFalse(self.session.complete_series(1))
        self.deliver()
        self.assertEqual(len(self.state.snapshot()["history"]), 1)
        self.assertEqual(self.state.snapshot()["history"][0]["repetitions"], 1)
        self.session.logout()
        self.deliver()
        self.assertEqual(self.state.snapshot()["stations"]["estacao01"]["status"], "LIVRE")

    def test_invalid_or_inactive_rfid_cannot_occupy(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "test.sqlite3")
            database.init_db(db)
            database.upsert_student("Ativo", "AA:BB:CC:DD", "Rosca Biceps", 1, db_path=db)
            database.upsert_student("Inativo", "11:22:33:44", "Rosca Biceps", 1, ativo=0, db_path=db)
            for uid in ("FF:FF:FF:FF", "11:22:33:44", "invalido"):
                self.assertFalse(self.session.login(database.get_student_by_uid(uid, db)))
            self.assertEqual(self.events, [])
            self.assertTrue(self.session.login(database.get_student_by_uid("AA BB CC DD", db)))

    @unittest.skipUnless(hasattr(os, "openpty"), "PTY disponivel apenas em Unix")
    def test_serial_rfid_flow_without_hardware(self):
        master, slave = os.openpty()
        try:
            with serial.Serial(os.ttyname(slave), 9600, timeout=0.1) as port:
                os.write(master, b"UID:FF:FF:FF:FF\n")
                time.sleep(0.05)
                invalid = serial_io.read_id(port)
                self.assertEqual(invalid, "FF:FF:FF:FF")
                with tempfile.TemporaryDirectory() as folder:
                    db = str(Path(folder) / "test.sqlite3")
                    database.init_db(db)
                    database.upsert_student("Ativo", "AA:BB:CC:DD", "Rosca Biceps", 1, db_path=db)
                    self.assertFalse(self.session.login(database.get_student_by_uid(invalid, db)))
                    os.write(master, b"UID:AA:BB:CC:DD\n")
                    time.sleep(0.05)
                    valid = serial_io.read_id(port)
                    self.assertTrue(self.session.login(database.get_student_by_uid(valid, db)))
        finally:
            os.close(master)
            os.close(slave)

    def test_retained_performance_and_duplicate_are_ignored(self):
        self.session.login(self.student)
        self.session.complete_series(1)
        topic = self.config.topic("estacao01", "performance")
        raw = json.dumps(self.events[-1][1]).encode()
        self.assertFalse(self.state.accept(topic, raw, True, self.config))
        self.assertTrue(self.state.accept(topic, raw, False, self.config))
        self.assertFalse(self.state.accept(topic, raw, False, self.config))
        self.assertEqual(len(self.state.snapshot()["history"]), 1)

    def test_cp4_counter_still_requires_equipment_and_full_motion(self):
        counter = BicepCurlCounter(160, 45)
        for angle in (170, 30, 170):
            self.assertFalse(counter.update(angle, True, False))
        self.assertFalse(counter.update(170, True, True))
        self.assertFalse(counter.update(30, True, True))
        self.assertTrue(counter.update(170, True, True))

    def test_web_routes_and_sse(self):
        client = create_app(self.state).test_client()
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(client.get("/api/state").json["history"], [])
        response = client.get("/events", buffered=False)
        self.assertIn(b"data:", next(response.response))
        response.close()


if __name__ == "__main__":
    unittest.main()
