import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, ".vortex_settings.json")

VERSION = "0.2"

# Настройки по умолчанию (приходят из гита)
DEFAULT_SETTINGS = {
    "auto_update": True,
    "theme": "dark",
    "history_limit": 1000,
}

class VortexConfig:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        """Загружает пользовательские настройки поверх дефолтных"""
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    user_settings = json.load(f)
                    self.settings.update(user_settings)
            except:
                pass

    def save(self):
        """Сохраняет только измененные настройки"""
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save()

# Глобальный объект конфига
config = VortexConfig()
