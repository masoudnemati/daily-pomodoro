import json

CONFIG_FILE = "configs.json"


class ConfigManager:
    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = filepath
        self.load()

    def load(self):
        with open(self.filepath, "r") as f:
            data = json.load(f)

        self.start_hour = data["start_day_hour"]
        self.end_hour = data["end_day_hour"]
        self.y_position = data["y_position"]
        self.country = data["location"]["country"]
        self.city = data["location"]["city"]

    def save(self, y_position):
        with open(self.filepath, "w") as f:
            json.dump(
                {
                    "start_day_hour": self.start_hour,
                    "end_day_hour": self.end_hour,
                    "y_position": y_position,
                    "location": {
                        "country": self.country,
                        "city": self.city,
                    },
                },
                f,
                indent=2,
            )