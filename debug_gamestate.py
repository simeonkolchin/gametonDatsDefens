
LOCAL_GAME_STATE = {
  "base": [
    {
      "attack": 10,
      "health": 100,
      "id": "base-block-1",
      "isHead": True,
      "lastAttack": {
        "x": 1,
        "y": 1
      },
      "range": 5,
      "x": 1,
      "y": 1
    },
    {
      "attack": 10,
      "health": 100,
      "id": "base-block-2",
      "isHead": False,
      "lastAttack": {
        "x": 2,
        "y": 2
      },
      "range": 5,
      "x": 2,
      "y": 2
    }
  ],
  "enemyBlocks": [
    {
      "attack": 10,
      "health": 100,
      "isHead": True,
      "lastAttack": {
        "x": 3,
        "y": 3
      },
      "name": "enemy-1",
      "x": 3,
      "y": 3
    },
    {
      "attack": 10,
      "health": 100,
      "isHead": False,
      "lastAttack": {
        "x": 4,
        "y": 4
      },
      "name": "enemy-2",
      "x": 4,
      "y": 4
    }
  ],
  "player": {
    "enemyBlockKills": 200,
    "gameEndedAt": "2021-10-10T10:00:00Z",
    "gold": 200,
    "name": "player-test",
    "points": 200,
    "zombieKills": 200
  },
  "realmName": "map1",
  "turn": 2,
  "turnEndsInMs": 2000,
  "zombies": [
    {
      "attack": 10,
      "direction": "up",
      "health": 100,
      "id": "zombie-1",
      "speed": 10,
      "type": "normal",
      "waitTurns": 1,
      "x": 5,
      "y": 5
    },
    {
      "attack": 10,
      "direction": "down",
      "health": 100,
      "id": "zombie-2",
      "speed": 10,
      "type": "normal",
      "waitTurns": 2,
      "x": 6,
      "y": 6
    }
  ]
}