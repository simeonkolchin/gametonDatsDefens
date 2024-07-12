import requests
import json
import time
import logging

logging.basicConfig(filename='game_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

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

def log_and_save_game_state(game_state, filename="game_state.json"):
    with open(filename, 'w') as f:
        json.dump(game_state, f, indent=4)
    logging.info(f"Game state saved to {filename}")

def build_map(game_state, map_filename="game_map.txt"):
    map_data = {}
    if "base" in game_state:
        for block in game_state["base"]:
            map_data[(block["x"], block["y"])] = 'B'  # B - Base block
    if "zombies" in game_state:
        for zombie in game_state["zombies"]:
            map_data[(zombie["x"], zombie["y"])] = 'Z'  # Z - Zombie

    if not map_data:
        return

    # Определение границ карты
    all_coords = map_data.keys()
    min_x = min(coord[0] for coord in all_coords)
    max_x = max(coord[0] for coord in all_coords)
    min_y = min(coord[1] for coord in all_coords)
    max_y = max(coord[1] for coord in all_coords)
    
    # Построение карты
    with open(map_filename, 'w') as f:
        for y in range(min_y, max_y + 1):
            line = ""
            for x in range(min_x, max_x + 1):
                if (x, y) in map_data:
                    line += map_data[(x, y)]
                else:
                    line += '.'
            f.write(line + "\n")
    logging.info(f"Game map saved to {map_filename}")

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
        
        log_and_save_game_state(game_state)
        build_map(game_state)
        
        command = strategy(game_state)

        game_api.send_commands(command)

        time.sleep(0.5)

if __name__ == "__main__":
    main()
