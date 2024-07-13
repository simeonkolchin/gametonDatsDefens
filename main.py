import requests
import json
import time
import logging
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import math

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

DEBUG = False

def log_and_save_game_state(game_state, filename="game_state.json"):
    with open(filename, 'w') as f:
        json.dump(game_state, f, indent=4)
    logging.info(f"Game state saved to {filename}")

def build_map(game_state, shots, block_shots, buildings, map_filename="game_map.txt"):
    map_data = {}
    if "base" in game_state and game_state['base'] is not None:
        for block in game_state["base"]:
            map_data[(block["x"], block["y"])] = 'B'  # B - Base block
    if "zombies" in game_state and game_state['zombies'] is not None:
        for zombie in game_state["zombies"]:
            map_data[(zombie["x"], zombie["y"])] = f'Z{zombie["health"]}'  # Z{health} - Zombie with health

    if "enemyBlocks" in game_state and game_state["enemyBlocks"] is not None:
        for block in game_state["enemyBlocks"]:
            if block.get("isHead"):
                map_data[(block["x"], block["y"])] = 'enemy_head'  # E - Enemy head block
            else:
                map_data[(block["x"], block["y"])] = 'enemy_base'  # b - Enemy base block

    try:
        if 'world' in game_state:
            for x in game_state['world']:
                if x['type'] == 'wall':
                    map_data[(x['x'], x['y'])] = "wall"
                elif x['type'] == 'default':
                    map_data[(x['x'], x['y'])] = 'spot'
    except:
        print('Ошибка в build_map создание стен')

    if not map_data:
        return

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
    visualize_map(game_state, map_data, min_x, max_x, min_y, max_y, shots, block_shots, buildings)

def visualize_map(game_state, map_data, min_x, max_x, min_y, max_y, shots, block_shots, buildings):
    fig, ax = plt.subplots()
    for (x, y), value in map_data.items():
        if value == 'H':
            color = 'blue'  # Head block (Control center)
        elif value == 'B':
            color = 'green'
        elif value == 'enemy_head':
            color = 'purple'
        elif value == 'enemy_base':
            color = 'pink'
        elif value.startswith('Z'):
            color = 'red'
            zombie_hp = value[1:]
            ax.text(x + 0.5, y + 0.5, zombie_hp, color='white', ha='center', va='center')
        elif value == 'wall':
            color = 'gray'
        elif value == 'spot':
            color = 'orange'
        else:
            color = 'white'
        rect = patches.Rectangle((x, y), 1, 1, linewidth=1, edgecolor='black', facecolor=color)
        ax.add_patch(rect)

    for start, end in shots:
        ax.arrow(start[0] + 0.5, start[1] + 0.5, end[0] - start[0], end[1] - start[1], head_width=0.1, head_length=0.3, fc='grey', ec='grey')
    for start, end in block_shots:
        ax.arrow(start[0] + 0.5, start[1] + 0.5, end[0] - start[0], end[1] - start[1], head_width=0.1, head_length=0.3, fc='black', ec='black')
    for x, y in buildings:
        ax.plot(x + 0.5, y + 0.5, marker='^', color='black', markersize=12)

    player_info = game_state["player"]
    player_text = f"Name: {player_info['name']} Gold: {player_info['gold']} Points: {player_info['points']} Zombie Kills: {player_info['zombieKills']} Enemy Block Kills: {player_info['enemyBlockKills']}"
    plt.text(min_x - 1, max_y + 2, player_text, fontsize=5, bbox=dict(facecolor='white', alpha=0.5))

    plt.xlim(min_x - 1, max_x + 1)
    plt.ylim(min_y - 1, max_y + 1)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig("game_map_visualized.png")
    logging.info("Game map visualized and saved to game_map_visualized.png")

def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def minimum_distance(main_point, other_points):
    x0, y0 = main_point
    distances = [euclidean_distance(x0, y0, x, y) for x, y in other_points]
    return min(distances)

def find_build_coords(base_blocks, map_data, game_state):
    """Ищет доступные координаты для строительства новых клеток рядом с существующими блоками базы."""
    new_coords = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    zombie_spots = []
    if 'world' in game_state and game_state['world'] is not None:
        for x in game_state['world']:
            if x['type'] == 'default':
                zombie_spots.append((x['x'], x['y']))
    
    for block in base_blocks:
        for dx, dy in directions:
            new_coord = (block["x"] + dx, block["y"] + dy)
            
            if new_coord not in map_data:
                if len(zombie_spots):
                    new_coords.append((new_coord[0], new_coord[1], minimum_distance(new_coord, zombie_spots)))
                else:
                    new_coords.append(new_coord)

    if len(zombie_spots):
        new_coords.sort(key=lambda x: x[2], reverse=True)

    return new_coords

def attack_enemy_bases(game_state, command):
    shots = []
    # Атакуем чужие базы
    if "base" in game_state and game_state['base'] is not None and "enemyBlocks" in game_state and game_state['enemyBlocks'] is not None:
        base_blocks = game_state["base"]
        enemy_blocks = game_state["enemyBlocks"]

        for block in base_blocks:
            block_id = block["id"]
            x, y = block["x"], block["y"]
            attack_radius = block["range"]

            for i in range(len(enemy_blocks)):
                ex, ey = enemy_blocks[i]["x"], enemy_blocks[i]["y"]
                distance = ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5
                if distance <= attack_radius and enemy_blocks[i]['health'] > 0:
                    print(f'ATTACK BASE: {block_id} - {ex} - {ey}')
                    command.add_attack(block_id, ex, ey)
                    enemy_blocks[i]['health'] -= block['attack']
                    shots.append(((x,y),(ex,ey)))
                    break
    return shots


# def filter_zombies_by_direction(zombies, base_blocks, turns=10):
#     potential_zombies = []
#     other_zombies = []

#     for zombie in zombies:
#         zx, zy = zombie["x"], zombie["y"]
#         direction = zombie["direction"]
        
#         if zombie['type'] == 'chaos_knight':
#             potential_zombies.append(zombie)
#             continue

#         path = [(zx, zy)]
#         current_x, current_y = zx, zy

#         for _ in range(20):
#             if direction == "up":
#                 current_y -= 1
#             elif direction == "down":
#                 current_y += 1
#             elif direction == "left":
#                 current_x -= 1
#             elif direction == "right":
#                 current_x += 1
#             path.append((current_x, current_y))

#         # Проверить, попадает ли зомби на блок базы
#         for bx, by in [(block["x"], block["y"]) for block in base_blocks]:
#             if (bx, by) in path:
#                 potential_zombies.append(zombie)
#                 continue
#         other_zombies.append(zombie)
        

#     return potential_zombies, other_zombies


def attack_zombies(game_state, command):
    zombies = [[z['x'], z['y'], z['health']] for z in game_state['zombies']]
    shots = []
    for block in game_state['base']:
        block_id = block["id"]
        x, y = block["x"], block["y"]
        attack_radius = block["range"]
        
        for i in range(len(zombies)):
            zx, zy, zhp = zombies[i]
            distance = ((x - zx) ** 2 + (y - zy) ** 2) ** 0.5
            if distance <= attack_radius and zhp > 0:
                command.add_attack(block_id, zx, zy)
                shots.append(((x, y), (zx, zy)))
                print('attack - ', zombies[i][2], block['attack'])
                zombies[i][2] -= block['attack']
                break
    return shots


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

    shots, block_shots, buildings = [], [], []

    print("START")

    if "base" in game_state and game_state['base'] is not None and "zombies" in game_state and game_state['zombies'] is not None:
        base_blocks = game_state["base"]
        map_data = {(block["x"], block["y"]): 'B' for block in base_blocks}
    
        for zombie in game_state["zombies"]:
            map_data[(zombie["x"], zombie["y"])] = 'Z'

        if 'world' in game_state:
            for x in game_state['world']:
                if x['type'] == 'wall':
                    map_data[(x['x'], x['y'])] = "wall"
                elif x['type'] == 'default':
                    map_data[(x['x'], x['y'])] = 'spot'

        shots = attack_zombies(game_state, command)
        block_shots = attack_enemy_bases(game_state, command)

        for zombie in game_state["zombies"]:
            base_blocks = handle_zombie_attack(zombie, base_blocks, map_data)


        # TODO: вот это прочекать, норм / не норм
        if game_state["player"]["gold"] > 0:
            build_coords = find_build_coords(base_blocks, map_data, game_state)
            # connected_blocks = get_connected_blocks(base_blocks)
            for coord in build_coords[:game_state["player"]["gold"]]:  # Ограничиваем количество новых блоков количеством золота
                # if coord in connected_blocks:
                    command.add_build(coord[0], coord[1])
                    print(f'BUILD: {coord[0]} - {coord[1]}')
                    buildings.append((coord[0], coord[1]))

        if base_blocks:
            
            if 'enemyBlocks' in game_state and game_state['enemyBlocks'] is not None:
                enemy_blocks = [(block['x'], block['y']) for block in game_state['enemyBlocks']]
                my_blocks = [(block['x'], block['y']) for block in base_blocks]

                for my_block in my_blocks:
                    safe = True
                    for enemy_block in enemy_blocks:
                        distance = ((my_block[0] - enemy_block[0]) ** 2 + (my_block[1] - enemy_block[1]) ** 2) ** 0.5
                        if distance < 6:
                            safe = False
                            break
                    if safe:
                        command.set_move_base(my_block[0], my_block[1])
                        break
            else:
                command.set_move_base(base_blocks[0]["x"], base_blocks[0]["y"])

    return command, shots, block_shots, buildings

def get_walls(world):
    if world is None:
        return

    walls = [(x['x'], x['y']) for x in world if x['type'] == 'wall']
    print('WALLS:', walls)

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

            if not DEBUG:
                world = game_api.get_world_info()
                if world is not None and 'zpots' in world:
                    game_state['world'] = world['zpots']

            if game_state is None:
                break
            
            if not DEBUG:
                with open(f'games/{hour}_{minute}_{tmp_num}.json', 'w') as file:
                    json.dump(game_state, file, indent=4)
                tmp_num += 1

            log_and_save_game_state(game_state)

            command, shots, block_shots, buildings = strategy(game_state)
            game_api.send_commands(command)

            try:
                build_map(game_state, shots, block_shots, buildings)
            except:
                print('Ошибка в build_map')

            time.sleep(0.25)

if __name__ == "__main__":
    main()
