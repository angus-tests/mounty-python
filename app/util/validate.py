
from app.exceptions.config_exception import ConfigException
from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface
from app.util.config import ConfigManager, ConfigType


def validate_config(self, 
                    config_manager: ConfigManager,
                    required_keys: list[str],
                    fs_repository: FileSystemRepositoryInterface):
    """
    Given a set of required keys, ensure they are all present in the config
    and also check any required files / folders exist
    """

    # Check the required keys are present
    missing_keys = [key for key in required_keys if not config_manager.get_config(key)]
    if missing_keys:
        raise ConfigException(f"Missing required configuration variables: {missing_keys}")
    
    # Check the required files / folders exist
    missing_files = []
    missing_folders = []
    for key in required_keys:
        config_type = config_manager.get_config_type(key)
        config_value = config_manager.get_config(key)

        if config_type == ConfigType.FILE_PATH:
            if not fs_repository.file_exists(config_value):
                missing_files.append(config_value)

        elif config_type == ConfigType.FOLDER_PATH:
            if not fs_repository.folder_exists(config_value):
                missing_folders.append(config_value)
    
    # Raise an exception if any required files / folders are missing
    if missing_files and missing_folders:
        raise ConfigException(f"Missing required files: {missing_files} and folders: {missing_folders}")
    elif missing_files:
        raise ConfigException(f"Missing required files: {missing_files}")
    elif missing_folders:
        raise ConfigException(f"Missing required folders: {missing_folders}")
    
        

