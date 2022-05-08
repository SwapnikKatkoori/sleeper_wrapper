from .base_api import BaseApi
import json
from pathlib import Path


class Player(object):
    def __init__(self, *player_dict, **kwargs):
        for dictionary in player_dict:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])


class Players(BaseApi):
    def __init__(self):
        pass

    def get_all_players(self):
        dir_path = Path('data/players')
        file_path = Path('data/players/all_players.json')

        if file_path.exists() and dir_path.exists():
            print("Local path and file exists, reading local version")
            with open(file_path) as json_file:
                all_players = json.load(json_file)
        else:
            print("local path and file not found, making API call")
            dir_path.mkdir(parents=True, exist_ok=True)
            all_players = self._call("https://api.sleeper.app/v1/players/nfl")
            with open(file_path, 'w') as outfile:
                json.dump(all_players, outfile)

        player_dict = {}
        for player in all_players:
            cur_dict = all_players[player]
            new_player = Player(cur_dict)
            player_dict[player] = new_player
        return player_dict

    def get_trending_players(self, sport, add_drop, hours=24, limit=25):
        return self._call(
            "https://api.sleeper.app/v1/players/{}/trending/{}?lookback_hours={}&limit={}".format(sport, add_drop,
                                                                                                  hours, limit))
    def check_cache(self):
        dir_path = Path('data/players')
        file_path = Path('data/players/all_players.json')

        print(f"Dir {dir_path} exists:  {dir_path.exists()}")
        print(f"File {file_path} exists: {file_path.exists()}")
        return dir_path.is_dir() and file_path.exists()