import requests
import json
import time
import os
from datetime import datetime

# Токен авторизации, полученный при регистрации
TOKEN = "YOUR_TOKEN_HERE"

# URL для игры
BASE_URL = "https://games.datsteam.dev/play/zombidef"

# Заголовок для авторизации
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
    def __init__(self, token):
        self.token = token
        self.base_url = "https://games.datsteam.dev/play/zombidef"
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": "application/json"
        }

    def register_for_round(self):
        url = f"{self.base_url}/participate"
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

    def check_rounds(self):
        url = f"{self.base_url}/rounds/zombidef"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get rounds: {response.status_code}, {response.text}")
            return None

def strategy(game_state):
    command = Command()
    
    # Получаем ID всех блоков базы
    base_blocks = game_state["base"]
    gold = game_state["player"]["gold"]
    
    if base_blocks:
        # Атака зомби если они в радиусе атаки
        for block in base_blocks:
            block_id = block["id"]
            x, y = block["x"], block["y"]
            attack_radius = block["range"]
            
            for zombie in game_state["zombies"]:
                zx, zy = zombie["x"], zombie["y"]
                distance = ((x - zx) ** 2 + (y - zy) ** 2) ** 0.5
                if distance <= attack_radius:
                    command.add_attack(block_id, zx, zy)
    
    # Построение новых клеток, если есть золото
    if gold > 0:
        build_coords = find_build_coords(base_blocks)
        for coord in build_coords:
            command.add_build(coord[0], coord[1])
    
    # Перемещение центра управления
    if base_blocks:
        command.set_move_base(base_blocks[0]["x"], base_blocks[0]["y"])

    return command

def find_build_coords(base_blocks):
    """Ищет доступные координаты для строительства новых клеток рядом с существующими блоками базы."""
    new_coords = []
    existing_coords = {(block["x"], block["y"]) for block in base_blocks}
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for block in base_blocks:
        for dx, dy in directions:
            new_coord = (block["x"] + dx, block["y"] + dy)
            if new_coord not in existing_coords:
                new_coords.append(new_coord)
    
    return new_coords[:1]  # Возвращаем только одну координату для построения одной клетки за ход

def save_game_state(game_state, filename="game_state.json"):
    with open(filename, 'w') as f:
        json.dump(game_state, f, indent=4)

def load_game_state(filename="game_state.json"):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return None

def main():
    game_api = GameAPI(TOKEN)
    
    while True:
        # Проверка информации о раундах
        rounds_info = game_api.check_rounds()
        if rounds_info:
            now = datetime.strptime(rounds_info["now"], "%Y-%m-%dT%H:%M:%SZ")
            for round_info in rounds_info["rounds"]:
                start_time = datetime.strptime(round_info["startAt"], "%Y-%m-%dT%H:%M:%SZ")
                if round_info["status"] == "active" and now < start_time:
                    time_to_start = (start_time - now).total_seconds()
                    print(f"Next round starts in {time_to_start} seconds.")
                    time.sleep(time_to_start)
                    game_api.register_for_round()
                    break
        
        # Получение текущего состояния игры
        game_state = game_api.get_game_state()
        if game_state is None:
            break
        
        # Сохранение состояния игры
        save_game_state(game_state)
        
        # Применение стратегии
        command = strategy(game_state)
        
        # Отправка команд
        game_api.send_commands(command)
        
        # Ожидание до следующего хода (2 секунды)
        time.sleep(2)

if __name__ == "__main__":
    main()
