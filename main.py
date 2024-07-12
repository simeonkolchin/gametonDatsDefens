import requests
import json
import time

# Токен авторизации, полученный при регистрации
TOKEN = "YOUR_TOKEN_HERE"

# URL для игры
BASE_URL = "https://games.datsteam.dev/play/zombidef"

# Заголовок для авторизации
HEADERS = {
    "X-Auth-Token": TOKEN,
    "Content-Type": "application/json"
}

def register_for_round():
    url = f"{BASE_URL}/participate"
    response = requests.put(url, headers=HEADERS)
    if response.status_code == 200:
        print("Registered for round successfully!")
    else:
        print(f"Failed to register for round: {response.status_code}, {response.text}")

def get_game_state():
    url = f"{BASE_URL}/units"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get game state: {response.status_code}, {response.text}")
        return None

def build_cells(coordinates):
    url = f"{BASE_URL}/command"
    payload = {
        "build": [{"x": coord[0], "y": coord[1]} for coord in coordinates]
    }
    response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code == 200:
        print("Build command accepted!")
    else:
        print(f"Failed to send build command: {response.status_code}, {response.text}")

def attack_cells(targets):
    url = f"{BASE_URL}/command"
    payload = {
        "attack": [{"x": target[0], "y": target[1]} for target in targets]
    }
    response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    if response.status_code == 200:
        print("Attack command accepted!")
    else:
        print(f"Failed to send attack command: {response.status_code}, {response.text}")

def main():
    # Регистрация на раунд
    register_for_round()
    
    while True:
        # Получение текущего состояния игры
        game_state = get_game_state()
        if game_state is None:
            break
        
        # Пример координат для постройки новых клеток базы
        build_coords = [(1, 1), (1, 2)]
        build_cells(build_coords)
        
        # Пример координат для атаки
        attack_coords = [(5, 5), (6, 6)]
        attack_cells(attack_coords)
        
        # Ожидание до следующего хода (2 секунды)
        time.sleep(2)

if __name__ == "__main__":
    main()
