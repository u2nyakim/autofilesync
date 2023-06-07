from configparser import ConfigParser


class ConfigService:
    def __init__(self, filename):
        self.cfg = ConfigParser()
        self.cfg.read(filename)

    def get(self, name: str, default=None):
        n = name.split(".")
        if len(n) == 2:
            if n[1]:
                value = self.cfg.get(n[0], n[1])
            else:
                value = dict(self.cfg.items(n[0]))
            if value is None:
                return default
            return value
        return None

    def getBoolean(self, name: str, default=None):
        value = self.get(name, default)
        if isinstance(value, str):
            value = value.lower()
            return value == 'true' or value == '1' or value == 'yes'
        return value is not None

    def getInt(self, name: str, default=None):
        value = self.get(name, default)
        if value is None:
            return 0
        return int(value)

    def getFloat(self, name: str, default=None):
        value = self.get(name, default)
        if value is None:
            return 0
        return float(value)
