
from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface
from app.interfaces.mount_repository_interface import MountRepositoryInterface
from app.interfaces.run_strategy_interface import RunStrategyInterface
from app.util.config import ConfigManager
from app.util.validate import validate_config


class FstabStrategy(RunStrategyInterface):
    """
    Concrete implementation of the RunStrategyInterface
    for use with an FSTAB file
    """

    def __init__(self, 
                 mount_repository: MountRepositoryInterface,
                 config_manager: ConfigManager,
                 fs_repository: FileSystemRepositoryInterface):
        self.mount_repository = mount_repository
        self.config_manager = config_manager
        self.fs_repository = fs_repository

    def validate(self):
        """
        Ensure we have the required config and files to run the FSTAB strategy
        """

        # For the FSTAB strategy we require the FSTAB_LOCATION and PROC_MOUNTS_LOCATION
        core_config = ConfigManager.get_core_config([
            "FSTAB_LOCATION",
            'PROC_MOUNTS_LOCATION'
        ])

        # Validate the core config and raise an exception if any are missing
        validate_config(
            self.config_manager,
            core_config,
            self.fs_repository
        )

    def main(self):
        pass

    def dry_run(self):
        pass

    def unmount_all(self):
        pass

    def info(self):
        pass