"""Station session events, independent of camera and network transport."""
from datetime import datetime, timezone
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class StationSession:
    def __init__(self, station_id, publish):
        self.station_id = station_id
        self.publish = publish
        self.student = None
        self.session_id = None
        self.completed = False

    def status(self):
        return {"event_id": str(uuid4()), "station_id": self.station_id,
                "status": "OCUPADA" if self.student else "LIVRE",
                "student_id": self.student["id"] if self.student else None,
                "student_name": self.student["nome"] if self.student else None,
                "session_id": self.session_id, "timestamp": now()}

    def login(self, student):
        # The caller provides only a student returned by the active RFID lookup.
        if self.student is not None or not student or not student.get("id"):
            return False
        self.student = student
        self.session_id = str(uuid4())
        self.completed = False
        self.publish("status", self.status())
        return True

    def complete_series(self, repetitions):
        if self.student is None or self.completed or repetitions < self.student["repeticoes"]:
            return False
        self.completed = True
        self.publish("performance", {
            "event_id": str(uuid4()), "station_id": self.station_id,
            "student_id": self.student["id"], "student_name": self.student["nome"],
            "exercise": self.student["exercicio"], "repetitions": repetitions,
            "series_id": f"{self.session_id}-1", "session_id": self.session_id,
            "timestamp": now(),
        })
        return True

    def logout(self):
        if self.student is None:
            return False
        self.student = None
        self.session_id = None
        self.completed = False
        self.publish("status", self.status())
        return True
