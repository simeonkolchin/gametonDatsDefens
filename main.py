import requests
import json
import time
import logging
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs('logging',exist_ok=True)
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

        while True:
            response = requests.put(url, headers=self.headers)
            status_code, response_json = response.status_code, json.loads(response.text)

            if status_code == 200:
                logging.info("Registered for round successfully!")
                return
            elif status_code == 400 and response_json['errCode'] == 1001:
                logging.info(f'Ждем следующего раунда, {response_json["error"]}')
                time.sleep(0.5)
            else:
                logging.error(f"Failed to register for round: {response.status_code}, {response.text}")

    def get_game_state(self):
        url = f"{self.base_url}/units"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to get game state: {response.status_code}, {response.text}")
            return None

    def send_commands(self, command):
        url = f"{self.base_url}/command"
        payload = command.to_dict()
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 200:
            logging.info("Command accepted!")
        else:
            logging.error(f"Failed to send command: {response.status_code}, {response.text}")

def log_and_save_game_state(game_state, filename="game_state.json"):
    with open(filename, 'w') as f:
        json.dump(game_state, f, indent=4)
    logging.info(f"Game state saved to {filename}")


def find_build_coords(base_blocks, map_data):
    """Ищет доступные координаты для строительства новых клеток рядом с существующими блоками базы."""
    new_coords = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for block in base_blocks:
        for dx, dy in directions:
            new_coord = (block["x"] + dx, block["y"] + dy)
            if new_coord not in map_data:
                new_coords.append(new_coord)
    
    return new_coords

def build_map(game_state, map_filename="game_map.txt"):
    map_data = {}
    if "base" in game_state and game_state["base"] is not None:
        for block in game_state["base"]:
            if block.get("isHead"):
                map_data[(block["x"], block["y"])] = 'H'  # H - Head block (Control center)
            else:
                map_data[(block["x"], block["y"])] = 'B'  # B - Base block
    if "enemyBlocks" in game_state and game_state["enemyBlocks"] is not None:
        for block in game_state["enemyBlocks"]:
            if block.get("isHead"):
                map_data[(block["x"], block["y"])] = 'E'  # E - Enemy head block
            else:
                map_data[(block["x"], block["y"])] = 'b'  # b - Enemy base block
    if "zombies" in game_state and game_state["zombies"] is not None:
        for zombie in game_state["zombies"]:
            zombie_type = zombie["type"]
            map_data[(zombie["x"], zombie["y"])] = f'Z({zombie_type[0].upper()})'  # Z - Zombie with type initial
    if "walls" in game_state and game_state["walls"] is not None:
        for wall in game_state["walls"]:
            map_data[(wall["x"], wall["y"])] = 'W'  # W - Wall

    if not map_data:
        # Если нет данных для отображения, установим границы по умолчанию
        min_x, max_x, min_y, max_y = 0, 10, 0, 10
    else:
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
    
    # Визуализация карты
    visualize_map(game_state, map_data, min_x, max_x, min_y, max_y)

def visualize_map(game_state, map_data, min_x, max_x, min_y, max_y):
    fig, ax = plt.subplots()
    for (x, y), value in map_data.items():
        if value == 'H':
            color = 'blue'
        elif value == 'B':
            color = 'green'
        elif value == 'E':
            color = 'purple'
        elif value == 'b':
            color = 'pink'
        elif value.startswith('Z'):
            color = 'red'
        elif value == 'W':
            color = 'gray'
        else:
            color = 'white'
        rect = patches.Rectangle((x, y), 1, 1, linewidth=1, edgecolor='black', facecolor=color)
        ax.add_patch(rect)

    # Добавление информации о игроке
    player_info = game_state["player"]
    plt.text(min_x - 1, max_y + 2, f"Gold: {player_info['gold']}\nPoints: {player_info['points']}\nZombie Kills: {player_info['zombieKills']}\nEnemy Block Kills: {player_info['enemyBlockKills']}", fontsize=12, bbox=dict(facecolor='white', alpha=0.5))

    plt.xlim(min_x - 1, max_x + 1)
    plt.ylim(min_y - 1, max_y + 3)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig("game_map_visualized.png")
    plt.close(fig)
    logging.info("Game map visualized and saved to game_map_visualized.png")

def handle_zombie_attack(zombie, base_blocks, map_data):
    zombie_type = zombie["type"]
    zx, zy = zombie["x"], zombie["y"]

    if zombie_type == "normal":
        attack_coords = [(zx, zy)]
    elif zombie_type == "fast":
        attack_coords = [(zx, zy)]
    elif zombie_type == "bomber":
        attack_coords = [(zx + dx, zy + dy) for dx in range(-1, 2) for dy in range(-1, 2)]
    elif zombie_type == "liner":
        attack_coords = [(zx + dx, zy) for dx in range(-3, 4)] + [(zx, zy + dy) for dy in range(-3, 4)]
    elif zombie_type == "juggernaut":
        attack_coords = [(zx, zy)]
    elif zombie_type == "chaos_knight":
        attack_coords = [(zx, zy)]
    else:
        attack_coords = [(zx, zy)]
    
    updated_base_blocks = [block for block in base_blocks if (block["x"], block["y"]) not in attack_coords]
    for coord in attack_coords:
        if coord in map_data:
            del map_data[coord]
    
    return updated_base_blocks

def strategy(game_state):
    command = Command()

    if "base" in game_state and game_state["base"] is not None:
        base_blocks = game_state["base"]
        map_data = {(block["x"], block["y"]): 'B' for block in base_blocks}
        for block in base_blocks:
            if block.get("isHead"):
                map_data[(block["x"], block["y"])] = 'H'
    else:
        base_blocks = []
        map_data = {}

    if "zombies" in game_state and game_state["zombies"] is not None:
        for zombie in game_state["zombies"]:
            map_data[(zombie["x"], zombie["y"])] = f'Z({zombie["type"][0].upper()})'
    if "walls" in game_state and game_state["walls"] is not None:
        for wall in game_state["walls"]:
            map_data[(wall["x"], wall["y"])] = 'W'
    if "enemyBlocks" in game_state and game_state["enemyBlocks"] is not None:
        for block in game_state["enemyBlocks"]:
            map_data[(block["x"], block["y"])] = 'b'
            if block.get("isHead"):
                map_data[(block["x"], block["y"])] = 'E'
    
    if base_blocks:
        for block in base_blocks:
            block_id = block["id"]
            x, y = block["x"], block["y"]
            attack_radius = block["range"]
                
            for zombie in game_state["zombies"] if game_state["zombies"] is not None else []:
                zx, zy = zombie["x"], zombie["y"]
                distance = ((x - zx) ** 2 + (y - zy) ** 2) ** 0.5
                if distance <= attack_radius:
                    command.add_attack(block_id, zx, zy)

        if "zombies" in game_state and game_state["zombies"] is not None:
            for zombie in game_state["zombies"]:
                base_blocks = handle_zombie_attack(zombie, base_blocks, map_data)

    if game_state["player"]["gold"] > 0:
        build_coords = find_build_coords(base_blocks, map_data)
        for coord in build_coords[:game_state["player"]["gold"]]:  # Ограничиваем количество новых блоков количеством золота
            command.add_build(coord[0], coord[1])

    if base_blocks:
        command.set_move_base(base_blocks[0]["x"], base_blocks[0]["y"])

    return command


def main():
    game_api = GameAPI(BASE_URL, TOKEN)

    while True:

        #game_api.register_for_round()
        
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
