from app.facades.log_facade import LogFacade
from app.repositories.file_sytem_repository import FileSystemRepositoryInterface
from app.util.config import ConfigManager


class ValidationService:
    """
    This class is responsible for validating the current environment
    variables and system state.
    """

    def __init__(self, config_manager: ConfigManager, fs_repository: FileSystemRepositoryInterface):
        self.config_manager = config_manager
        self.fs_repository = fs_repository

    def validate(self) -> bool:
        """
        Validate the current environment variables and system state.
        :return True if the environment is valid, False otherwise
        """
        # List of configuration keys to validate
        files_to_validate = {
            "LINUX_SSH_LOCATION": "Linux SSH key not found",
            "CIFS_FILE_LOCATION": "CIFS file not found",
            "DESIRED_MOUNTS_FILE_PATH": "Desired mounts file not found",
            "FSTAB_LOCATION": "Fstab file not found",
            "PROC_MOUNTS_LOCATION": "Proc mounts file not found",
        }

        missing_files = []
        for config_key, error_message in files_to_validate.items():
            try:
                self._validate_file_exists(config_key, error_message)
            except FileNotFoundError:
                missing_files.append(config_key)

        # Log missing files
        if missing_files:
            LogFacade.log_table_error(
                "Missing the following files from the system",
                ["Filename"],
                [[self.config_manager.get_config(key)] for key in missing_files]
            )
        return len(missing_files) == 0

    def _validate_file_exists(self, config_key: str, error_message: str):
        """
        Validate that the file exists for the given configuration key.

        Args:
            config_key (str): The key to retrieve the file path from the config.
            error_message (str): The error message to raise if the file is not found.

        Raises:
            FileNotFoundError: If the file does not exist at the specified location.
        """
        file_path = self.config_manager.get_config(config_key)
        if not self.fs_repository.file_exists(file_path):
            raise FileNotFoundError(f"{error_message} at {file_path}")
