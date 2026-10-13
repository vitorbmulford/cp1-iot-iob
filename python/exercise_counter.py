"""Maquina de estados para contar apenas roscas biceps completas."""


class BicepCurlCounter:
    WAITING_EXTENSION = "Aguardando extensao inicial"
    WAITING_FLEXION = "Extensao confirmada - flexione o braco"
    WAITING_FINAL_EXTENSION = "Flexao confirmada - estenda o braco"

    def __init__(self, extended_angle, flexed_angle):
        self.extended_angle = extended_angle
        self.flexed_angle = flexed_angle
        self.reset()

    def reset(self):
        self.state = self.WAITING_EXTENSION

    def update(self, angle, pose_is_reliable, equipment_present):
        """Conta apenas extensao -> flexao -> extensao de uma rosca biceps."""
        if not equipment_present:
            self.reset()
            return False
        if not pose_is_reliable or angle is None:
            return False
        if self.state == self.WAITING_EXTENSION:
            if angle >= self.extended_angle:
                self.state = self.WAITING_FLEXION
        elif self.state == self.WAITING_FLEXION:
            if angle <= self.flexed_angle:
                self.state = self.WAITING_FINAL_EXTENSION
        elif self.state == self.WAITING_FINAL_EXTENSION:
            if angle >= self.extended_angle:
                self.reset()
                return True
        return False
