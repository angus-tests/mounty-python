from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions.config_exception import ConfigException
from app.facades.log_facade import LogFacade


class ConfigManager:
    def __init__(self):
        self.config = {}
        self.project_folder = Path(__file__).parent.parent.parent
        self.env_file_path = self.project_folder / '.env'

    def add_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)

    def load_from_env(self):
        # Load environment variables from .env file
        load_dotenv(self.env_file_path)

        # Add environment variables to config
        self.add_config('LINUX_SSH_LOCATION', getenv('LINUX_SSH_LOCATION'))
        self.add_config('LINUX_SSH_USER', getenv('LINUX_SSH_USER'))
        self.add_config('CIFS_FILE_LOCATION', getenv('CIFS_FILE_LOCATION'))
        self.add_config('DESIRED_MOUNTS_PATH', getenv('DESIRED_MOUNTS_FILE_PATH', 'mounts.json'))
        self.add_config('FSTAB_LOCATION', '/etc/fstab')
        self.add_config('PROJECT_FOLDER', self.project_folder)
        self.add_config('ENV_FILE_PATH', self.env_file_path)

        # Validate configuration
        self._validate_config()

    def __str__(self):
        table = [[key, value] for key, value in self.config.items()]
        return LogFacade.format_table("Configration variables", ["Key", "Value"], table)

    def _validate_config(self):
        """
        Check if all required configuration variables are set
        """
        required_keys = ['LINUX_SSH_LOCATION', 'LINUX_SSH_USER', 'CIFS_FILE_LOCATION']
        missing_keys = [key for key in required_keys if not self.get_config(key)]
        if missing_keys:
            raise ConfigException(f"Missing required configuration variables: {missing_keys}")

