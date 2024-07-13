import requests
from datetime import datetime, timedelta

# Токен авторизации, полученный при регистрации
TOKEN = "669018dfc12ad669018dfc12af"
BASE_URL = "https://games-test.datsteam.dev/play/zombidef"

HEADERS = {
    "X-Auth-Token": TOKEN,
    "Content-Type": "application/json"
}

def get_next_round_time():
    url = f"{BASE_URL}/rounds"
    response = requests.get('https://games-test.datsteam.dev/rounds/zombidef', headers=HEADERS)
    
    if response.status_code == 200:
        rounds_info = response.json()
        current_time = datetime.now()

        next_round_time = None
        min_time_diff = None

        for x in rounds_info['rounds']:

            print(x)
            print('---'*10)

        # for round_info in rounds_info:
        #     print(round_info['startTime'])

            # if round_start_time > current_time:
            #     time_diff = round_start_time - current_time

            #     if min_time_diff is None or time_diff < min_time_diff:
            #         min_time_diff = time_diff
            #         next_round_time = round_start_time

        # if next_round_time:
    #         print(f"Next round starts at: {next_round_time}")
    #         return next_round_time
    #     else:
    #         print("No upcoming rounds found.")
    #         return None
    # else:
    #     print(f"Failed to get round information: {response.status_code}, {response.text}")
    #     return None

# Пример вызова функции
next_round_time = get_next_round_time()
