import logging
import requests
import json
from debug_gamestate import LOCAL_GAME_STATE
import time

class GameAPI:
    def __init__(self, url, token, debug=False):
        self.token = token
        self.base_url = url
        self.debug = debug
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": "application/json"
        }
        self.hod_num = 1

    def register_for_round(self):
        if self.debug:
            logging.info("DEBUG mode: Skipping registration for round.")
        else:

            while True:
                url = f"{self.base_url}/participate"
                response = requests.put(url, headers=self.headers)
                print(response.status_code, response.text)
                if response.status_code == 200:
                    logging.info("Registered for round successfully!")
                    return
                else:
                    logging.error(f"Failed to register for round: {response.status_code}, {response.text}")
                    time.sleep(0.5)

    def get_game_state(self):
        if self.debug:
            logging.info("DEBUG mode: Using local game state.")

            with open(f'games/10_26_{min(self.hod_num, 30)}.json', 'r') as f:
                self.hod_num += 1
                game_state = json.load(f)
                return game_state
        else:
            url = f"{self.base_url}/units"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Failed to get game state: {response.status_code}, {response.text}")
                return None

    def send_commands(self, command):
        if self.debug:
            logging.info("DEBUG mode: Skipping sending commands.")
        else:
            url = f"{self.base_url}/command"
            payload = command.to_dict()
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            if response.status_code == 200:
                logging.info("Command accepted!")
            else:
                logging.error(f"Failed to send command: {response.status_code}, {response.text}")
