import requests
import json
import time
import logging
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

logging.basicConfig(filename='game_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

from gameapi import GameAPI
from command import Command

# Токен авторизации, полученный при регистрации
TOKEN = "669018dfc12ad669018dfc12af"
BASE_URL = "https://games-test.datsteam.dev/play/zombidef"

HEADERS = {
    "X-Auth-Token": TOKEN,
    "Content-Type": "application/json"
}

DEBUG = True

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
            # map_data[(zombie["x"], zombie["y"])] = 'Z'  # Z - Zombie
            map_data[(zombie["x"], zombie["y"])] = f'Z{zombie["health"]}'  # Z{health} - Zombie with health

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
    
    # Визуализация карты
    visualize_map(map_data, min_x, max_x, min_y, max_y)

def visualize_map(map_data, min_x, max_x, min_y, max_y):
    fig, ax = plt.subplots()
    for (x, y), value in map_data.items():
        if value == 'B':
            color = 'green'
        elif value.startswith('Z'):
            color = 'red'
            zombie_hp = value[1:]
            ax.text(x + 0.5, y + 0.5, zombie_hp, color='white', ha='center', va='center')
        else:
            color = 'white'
        rect = patches.Rectangle((x, y), 1, 1, linewidth=1, edgecolor='black', facecolor=color)
        ax.add_patch(rect)
    
    plt.xlim(min_x - 1, max_x + 1)
    plt.ylim(min_y - 1, max_y + 1)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig("game_map_visualized.png")
    logging.info("Game map visualized and saved to game_map_visualized.png")

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

def attack_enemy_bases(game_state, command):
    # Атакуем чужие базы
    if "base" in game_state and "enemyBlocks" in game_state:
        base_blocks = game_state["base"]
        enemy_blocks = game_state["enemyBlocks"]

        for block in base_blocks:
            block_id = block["id"]
            x, y = block["x"], block["y"]
            attack_radius = block["range"]

            for enemy_block in enemy_blocks:
                ex, ey = enemy_block["x"], enemy_block["y"]
                distance = ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5
                if distance <= attack_radius:
                    command.add_attack(block_id, ex, ey)


def filter_zombies_by_direction(zombies, base_blocks, turns=10):
    potential_zombies = []

    for zombie in zombies:
        zx, zy = zombie["x"], zombie["y"]
        direction = zombie["direction"]
        
        if zombie['type'] == 'chaos_knight':
            potential_zombies.append(zombie)
            continue

        # Рассчитать все клетки, куда зомби может попасть за несколько ходов
        path = [(zx, zy)]
        current_x, current_y = zx, zy

        for _ in range(20):
            if direction == "up":
                current_y -= 1
            elif direction == "down":
                current_y += 1
            elif direction == "left":
                current_x -= 1
            elif direction == "right":
                current_x += 1
            path.append((current_x, current_y))

        # Проверить, попадает ли зомби на блок базы
        for bx, by in [(block["x"], block["y"]) for block in base_blocks]:
            if (bx, by) in path:
                potential_zombies.append(zombie)
                break

    return potential_zombies


def attack_zombies(game_state, command):
    # Здесь выбираем зомби, по которым будем стрелять
    if "base" in game_state and "zombies" in game_state:
        base_blocks = game_state["base"]
        zombies = game_state["zombies"]

        filtered_zombies = filter_zombies_by_direction(zombies, base_blocks)
        zombie_list = [{"x": z["x"], "y": z["y"], "hp": z["health"], "id": z["id"], "type": z["type"], "speed": z["speed"]} for z in filtered_zombies]

        for block in base_blocks:
            block_id = block["id"]
            x, y = block["x"], block["y"]
            attack_radius = block["range"]
            attack_power = block["attack"]

            nearest_zombie_idx = None
            nearest_distance = float('inf')

            for idx, zombie in enumerate(zombie_list):
                zx, zy = zombie["x"], zombie["y"]
                distance = ((x - zx) ** 2 + (y - zy) ** 2) ** 0.5
                norm_distance = distance

                if zombie['type'] in ['liner']:
                    norm_distance -= 1
                elif zombie['type'] in ['bomber', 'juggernaut', 'chaos_knight']:
                    norm_distance -= 2

                if distance <= attack_radius and norm_distance < nearest_distance and zombie['hp'] > 0:
                    nearest_zombie_idx = idx
                    nearest_distance = norm_distance

            if nearest_zombie_idx:
                command.add_attack(block_id, zombie_list[nearest_zombie_idx]["x"], zombie_list[nearest_zombie_idx]["y"])
                zombie_list[nearest_zombie_idx]["hp"] -= attack_power

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


def get_connected_blocks(base_blocks):
    connected_blocks = set()
    to_visit = [block for block in base_blocks if block.get("isHead")]
    while to_visit:
        block = to_visit.pop()
        connected_blocks.add((block["x"], block["y"]))
        neighbors = [(block["x"] + dx, block["y"] + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]]
        for nx, ny in neighbors:
            if (nx, ny) not in connected_blocks:
                for b in base_blocks:
                    if b["x"] == nx and b["y"] == ny:
                        to_visit.append(b)
                        break
    return connected_blocks


def strategy(game_state):
    command = Command()

    print("START")

    if "base" in game_state:
        base_blocks = game_state["base"]
        map_data = {(block["x"], block["y"]): 'B' for block in base_blocks}
        if "zombies" in game_state:
            for zombie in game_state["zombies"]:
                map_data[(zombie["x"], zombie["y"])] = 'Z'

        print('START 2')

        attack_zombies(game_state, command)

        print("START 3")
        attack_enemy_bases(game_state, command)

        if "zombies" in game_state:
            for zombie in game_state["zombies"]:
                base_blocks = handle_zombie_attack(zombie, base_blocks, map_data)



        # TODO: вот это прочекать, норм / не норм
        if game_state["player"]["gold"] > 0:
            build_coords = find_build_coords(base_blocks, map_data)
            connected_blocks = get_connected_blocks(base_blocks)
            for coord in build_coords[:game_state["player"]["gold"]]:  # Ограничиваем количество новых блоков количеством золота
                if coord in connected_blocks:
                    command.add_build(coord[0], coord[1])

            # walls проверить, пока что хз
            # # Парсим стены и проверяем, чтобы новые блоки не строились на стенах
            # for wall in game_state["walls"] if game_state["walls"] is not None else []:
            #     wall_coords = (wall["x"], wall["y"])
            #     if wall_coords in build_coords:
            #         build_coords.remove(wall_coords)

        if base_blocks:
            # TODO: нужно находить блоки, где близко находится джегернаут или другой сильный зомби, которого нужно убить и туда поставить базу

            # Здесь нужно как то выбирать безопасные клетки, куда стоит установит базу
            # for block in base_blocks:
            #     for zombie in game_state["zombies"] if game_state["zombies"] is not None else []:
            #         if zombie["type"] in ["juggernaut", "chaos_knight"]:
            #             zx, zy = zombie["x"], zombie["y"]
            #             distance = ((block["x"] - zx) ** 2 + (block["y"] - zy) ** 2) ** 0.5
            #             if distance <= block["range"]:
            #                 command.add_attack(block["id"], zx, zy)

            command.set_move_base(base_blocks[0]["x"], base_blocks[0]["y"])

    return command

def main():
    game_api = GameAPI(BASE_URL, TOKEN, DEBUG)

    while True:

        game_api.register_for_round()

        cur_time = datetime.now()
        hour = cur_time.hour
        minute = cur_time.minute
        tmp_num = 1
        
        while True:
            game_state = game_api.get_game_state()
            if game_state is None:
                break
            
            if not DEBUG:
                with open(f'games/{hour}_{minute}_{tmp_num}.json', 'w') as file:
                    json.dump(game_state, file, indent=4)
                tmp_num += 1

            log_and_save_game_state(game_state)
            build_map(game_state)

            command = strategy(game_state)
            game_api.send_commands(command)
            time.sleep(0.5)

if __name__ == "__main__":
    main()
