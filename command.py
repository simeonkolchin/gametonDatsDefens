
class Command:
    def __init__(self):
        self.attacks = []
        self.builds = []
        self.move_base = None

    def add_attack(self, block_id, x, y):
        self.attacks.append({"blockId": block_id, "target": {"x": x, "y": y}})

    def add_build(self, x, y):
        self.builds.append({"x": x, "y": y})

    def set_move_base(self, x, y):
        self.move_base = {"x": x, "y": y}

    def to_dict(self):
        return {
            "attack": self.attacks,
            "build": self.builds,
            "moveBase": self.move_base if self.move_base else {}
        }
