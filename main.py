import requests
import json
import time

# Токен авторизации, полученный при регистрации
TOKEN = "669018dfc12ad669018dfc12af"
BASE_URL = "https://games-test.datsteam.dev/play/zombidef"

HEADERS = {
    "X-Auth-Token": TOKEN,
    "Content-Type": "application/json"
}

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

class GameAPI:
    def __init__(self, url, token):
        self.token = token
        self.base_url = url
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": "application/json"
        }

    def register_for_round(self):
        url = f"{self.base_url}/participate"

        print(url, self.headers)
        response = requests.put(url, headers=self.headers)
        if response.status_code == 200:
            print("Registered for round successfully!")
        else:
            print(f"Failed to register for round: {response.status_code}, {response.text}")

    def get_game_state(self):
        url = f"{self.base_url}/units"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get game state: {response.status_code}, {response.text}")
            return None

    def send_commands(self, command):
        url = f"{self.base_url}/command"
        payload = command.to_dict()
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("Command accepted!")
        else:
            print(f"Failed to send command: {response.status_code}, {response.text}")

def strategy(game_state):
    command = Command()

    base_blocks = game_state["base"]
    
    if base_blocks:
        for block in base_blocks:
            block_id = block["id"]
            x, y = block["x"], block["y"]
            attack_radius = block["range"]
            
            for zombie in game_state["zombies"]:
                zx, zy = zombie["x"], zombie["y"]
                distance = ((x - zx) ** 2 + (y - zy) ** 2) ** 0.5
                if distance <= attack_radius:
                    command.add_attack(block_id, zx, zy)

    if game_state["player"]["gold"] > 0:
        build_coords = [(1, 1), (1, 2)]
        for coord in build_coords:
            command.add_build(coord[0], coord[1])

    if base_blocks:
        command.set_move_base(base_blocks[0]["x"], base_blocks[0]["y"])

    return command

def main():
    game_api = GameAPI(BASE_URL, TOKEN)
    game_api.register_for_round()
    
    while True:
        game_state = game_api.get_game_state()
        if game_state is None:
            break

        command = strategy(game_state)

        game_api.send_commands(command)

        time.sleep(0.5)

if __name__ == "__main__":
    main()
