from os import getenv

from dotenv import load_dotenv
from tabulate import tabulate

from app.facades.log_facade import LogFacade


class ConfigManager:
    def __init__(self):
        self.config = {}

    def add_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)

    def load_from_env(self):
        # Load environment variables from .env file
        load_dotenv()

        # Add environment variables to config
        self.add_config('LINUX_SSH_LOCATION', getenv('LINUX_SSH_LOCATION'))
        self.add_config('LINUX_SSH_USER', getenv('LINUX_SSH_USER'))
        self.add_config('CIFS_FILE_LOCATION', getenv('CIFS_FILE_LOCATION'))
        self.add_config('FSTAB_LOCATION', "/etc/fstab")

    def __str__(self):
        table = [[key, value] for key, value in self.config.items()]
        return LogFacade.format_table("Configration variables", ["Key", "Value"], table)
