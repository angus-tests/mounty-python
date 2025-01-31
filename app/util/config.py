from enum import Enum
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions.config_exception import ConfigException
from app.facades.log_facade import LogFacade

class ConfigType(Enum):
    DEFAULT = "default"
    FILE_PATH = "file_path"
    FOLDER_PATH = "folder_path"

class ConfigManager:
    """
    Config Manager class handles storing and loading configuration variables
    """

    def __init__(self):

        # Initialize configuration dictionary
        self.config = {}

        # Store the project root folder and .env file path
        self.project_folder = Path(__file__).parent.parent.parent
        self.env_file_path = self.project_folder / '.env'

    def add_config(self, key: str, 
                   value: str, 
                   config_type: ConfigType = ConfigType.DEFAULT):
        """
        Add a configuration variable to the config dictionary
        :param key: str - The key of the configuration variable
        :param value: str - The value of the configuration variable
        :param config_type: ConfigType - The type of configuration variable
        e.g does the config represent a file path, folder path, etc.
        """
        
        self.config[key] = {
            "value": value,
            "config_type": config_type
        }

    def get_config(self, key: str) -> str:
        """
        Get a configuration variable from the config dictionary
        :param key: str - The key of the configuration variable
        :return: str - The value of the configuration variable
        """
        return self.config.get(key, {}).get("value")
    
    def get_config_type(self, key: str) -> ConfigType:
        """
        Get the type of a configuration variable from the config dictionary
        :param key: str - The key of the configuration variable
        :return: ConfigType - The type of the configuration variable
        """
        return self.config.get(key, {}).get("config_type")

    def load_from_env(self):
        """
        Load configuration variables from the .env file
        and populate the config dictionary
        """

        # Load environment variables from .env file into the environment
        load_dotenv(self.env_file_path)

        # Add environment variables to config
        self.add_config('LINUX_SSH_LOCATION',
                         getenv('LINUX_SSH_LOCATION'), 
                         ConfigType.FILE_PATH)
        
        self.add_config('LINUX_SSH_USER', 
                        getenv('LINUX_SSH_USER'))
        
        self.add_config('CIFS_FILE_LOCATION', 
                        getenv('CIFS_FILE_LOCATION'), 
                        ConfigType.FILE_PATH)
        
        self.add_config('CIFS_DOMAIN',
                         getenv('CIFS_DOMAIN', 'ONS'))
        
        self.add_config('DESIRED_MOUNTS_FILE_PATH', 
                        getenv('DESIRED_MOUNTS_FILE_PATH', 'mounts.json'),
                        ConfigType.FILE_PATH)
        
        self.add_config('FSTAB_LOCATION', 
                        '/etc/fstab', 
                        ConfigType.FILE_PATH)
        
        self.add_config('PROC_MOUNTS_LOCATION',
                         '/proc/mounts', 
                         ConfigType.FILE_PATH)
        
        self.add_config('PROJECT_FOLDER', 
                        self.project_folder, 
                        ConfigType.FOLDER_PATH)
        
        self.add_config('ENV_FILE_PATH', 
                        self.env_file_path, 
                        ConfigType.FILE_PATH)

    def __str__(self):
        table = [[key, value["value"]] for key, value in self.config.items()]
        return LogFacade.format_table("Configration variables", ["Key", "Value"], table)

    @staticmethod
    def get_core_config(extra_keys: list[str] = None) -> list[str]:
        """
        Return a list of core configuration keys
        :param extra_keys: list[str] - Any extra keys to add to the core config
        """
        core_keys = [
            'LINUX_SSH_LOCATION',
            'LINUX_SSH_USER',
            'CIFS_FILE_LOCATION',
            'CIFS_DOMAIN',
            'DESIRED_MOUNTS_FILE_PATH',
        ]

        if extra_keys:
            core_keys.extend(extra_keys)

        # Remove any duplicates
        core_keys = list(set(core_keys))

        return core_keys