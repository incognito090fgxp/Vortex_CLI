# -*- coding: utf-8 -*-
import json
import os
from ..registry import SETTINGS_PATH, ENV_PATH, HISTORY_PATH, PROJECT_ROOT, PACKAGE_DIR

# Версия: Release.Beta.DEV.FIX
VERSION = "0.3.2.3"
# Порог для маленьких экранов
SMALL_SCREEN_WIDTH = 65

# Настройки по умолчанию
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
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    user_settings = json.load(f)
                    self.settings.update(user_settings)
            except:
                pass

    def save(self):
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
