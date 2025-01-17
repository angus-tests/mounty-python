import json
import subprocess
from abc import ABC, abstractmethod

from app.enums.enums import MountType
from app.exceptions.cleanup_exception import CleanupException
from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.facades.log_facade import LogFacade
from app.factories.mount_factory import MountFactory
from app.models.mount import Mount
from app.repositories.file_sytem_repository import FileSystemRepositoryInterface
from app.repositories.mount_config_repository import MountConfigRepository
from app.util.config import ConfigManager


class MountRepositoryInterface(ABC):
    """
    Interface for a mount repository, which is responsible for
    providing the application with mounts to work with
    """

    @abstractmethod
    def get_desired_mounts(self) -> list[Mount]:
        """Fetch a list of mounts we want on the system"""
        pass

    @abstractmethod
    def get_current_mounts(self) -> list[Mount]:
        """Fetch a list of mounts currently on the system"""
        pass

    @abstractmethod
    def get_orphan_mounts(self) -> list[Mount]:
        """Fetch a list of mounts that are not present in config but are mounted on the system"""
        pass

    @abstractmethod
    def mount(self, mount: Mount):
        """
        mount a mount to the system
        :param mount: the mount to mount on the system
        """
        pass

    @abstractmethod
    def unmount(self, mount_path: str):
        """
        unmount a mount from the system
        :param mount_path: the path of the mount to unmount on the system
        """
        pass

    @abstractmethod
    def unmount_all(self) -> list[Mount]:
        """
        unmount all mounts from the system
        :return A list of mounts that failed to unmount
        """
        pass

    def cleanup(self):
        """
        Cleanup the system
        """


class MountRepository(MountRepositoryInterface):
    """
    Concrete implementation of a mount repository
    """

    def __init__(self,
                 config_manager: ConfigManager,
                 mount_config_repository: MountConfigRepository,
                 fs_repository: FileSystemRepositoryInterface,
                 mount_prefix="/shares"):
        """
        :param config_manager: ConfigManager - An instance of the config manager to fetch configuration variables
        :param mount_config_repository: MountConfigRepository - An instance of the mount config repository to fetch mount information from FSTAB etc
        :param fs_repository: FileSystemRepositoryInterface - An instance of the file system repository to interact with the file system
        :param mount_prefix: str - The prefix for the mounts we are interested in
        """
        self.config_manager = config_manager
        self.mount_config_repository = mount_config_repository
        self.fs_repository = fs_repository
        self.mount_prefix = mount_prefix

    def get_current_mounts(self) -> list[Mount]:
        """
        Get all the mounts on the system that we are interested in
        these are the ones that are prefixed with self.mount_prefix
        """

        # Fetch all the mounts on the system from the config repo
        all_system_mounts = self.mount_config_repository.get_all_system_mounts()

        current_mounts = []

        # Filter out the mounts that don't start with our mount prefix
        for mount in all_system_mounts:
            is_mount = self.mount_config_repository.is_mounted(mount.mount_path)

            if mount.mount_path.startswith(self.mount_prefix) and is_mount:
                current_mounts.append(mount)
            elif not is_mount and mount.mount_path.startswith(self.mount_prefix):
                LogFacade.warning(f"Mount {mount.mount_path} is present in the config but not mounted on the system")

        return current_mounts

    def get_desired_mounts(self) -> list[Mount]:
        """
        Read in the desired mounts from a .json file
        """

        # Read the desired mounts from the file
        mounts_data = json.loads(
            self.fs_repository.read_file(self.config_manager.get_config("DESIRED_MOUNTS_FILE_PATH"))
        )

        mounts = []

        for mount in mounts_data:

            if mount["mount_type"] == MountType.LINUX.value:
                # Add the linux user to the mount
                mount["actual_path"] = f"{self.config_manager.get_config('LINUX_SSH_USER')}@{mount['actual_path']}"

            # Append the mount to the list
            mounts.append(MountFactory.create_from_json(mount))

        return mounts

    def get_orphan_mounts(self) -> list[Mount]:

        # Fetch all the mounts on the system from the config repo
        all_system_mounts = self.mount_config_repository.get_all_system_mounts()

        return [
            mount
            for mount in all_system_mounts
            if mount.mount_path.startswith(self.mount_prefix) and not self.mount_config_repository.is_mounted(mount.mount_path)
        ]

    def mount(self, mount: Mount):
        """
        Add a mount to the system
        """

        # Create the mount point
        self._add_mount_point(mount.mount_path)

        # Store this mount information on the system to persist
        self.mount_config_repository.store_mount_information(mount)

        # Call the mount command
        self._perform_mount(mount.mount_path)

    def unmount(self, mount_path: str):
        """
        Remove a mount from the system
        :param mount_path: The local path of the mount to unmount
        """

        # If the mount point exists, check if it is empty
        self._validate_mount_point(mount_path)

        # Remove the mount information from the config
        self.mount_config_repository.remove_mount_information(mount_path)

        # Unmount
        self._perform_unmount(mount_path)

        # Remove the mount point
        self._remove_mount_point(mount_path, check_empty=False)

    def unmount_all(self) -> list[Mount]:
        """
        Unmount all mounts from the system that start with our mount prefix.
        :return: List of failed mounts
        """

        # Fetch all the mounts on the system from the config repo
        all_mounts = self.get_current_mounts()

        # Remove all the mounts from the config
        self.mount_config_repository.remove_mounts(all_mounts)

        failed_to_unmount = []

        for mount in all_mounts:
            try:
                self._validate_mount_point(mount.mount_path)
                self._perform_unmount(mount.mount_path)
                self._remove_mount_point(mount.mount_path, check_empty=False)
            except UnmountException as e:
                failed_to_unmount.append(mount)
                LogFacade.error(f"Failed to unmount {mount.mount_path}: {e}")

        return failed_to_unmount

    def cleanup(self):
        """
        Cleanup the configuration repository
        remove duplicates and fake mounts
        """
        try:
            self.mount_config_repository.cleanup()
        except Exception as e:
            raise CleanupException(f"Error cleaning up mount configuration: {e}")

    def _perform_unmount(self, mount_path: str):
        """
        Perform the actual unmount operation and handle errors.
        :param mount_path: The local path of the mount to unmount
        :return: True if successful, False otherwise
        """
        if not self.mount_config_repository.is_mounted(mount_path):
            LogFacade.warning(f"Attempted to unmount {mount_path} but it was already unmounted")
            return True

        umount_result = subprocess.run(["sudo", "umount", mount_path], capture_output=True)
        if umount_result.returncode != 0:
            raise UnmountException(umount_result.stderr)

        return True

    def _perform_mount(self, mount_path: str):
        """
        Perform the actual mount operation and handle errors.
        :param mount_path: The local path of the mount to mount
        """
        if self.mount_config_repository.is_mounted(mount_path):
            LogFacade.warning(f"Attempted to mount {mount_path} but it was already mounted")
            return True

        mount_result = subprocess.run(["sudo", "mount", mount_path], capture_output=True)
        if mount_result.returncode != 0:
            raise MountException(mount_result.stderr)

    def _remove_mount_point(self, mount_path: str, check_empty=True):
        """
        Remove the mount point directory.
        :param mount_path: The path to remove
        :param check_empty: Check if the mount point is empty before removing it
        """
        if check_empty:
            self._validate_mount_point(mount_path)
        try:
            self.fs_repository.remove_directory(mount_path)
        except Exception as e:
            raise UnmountException(f"Error removing mount point {mount_path}: {e}")

    def _add_mount_point(self, mount_path):
        """
        Add a mount point directory.
        :param mount_path: The path to add
        """
        try:
            # Create the mount point if it doesn't exist
            if not self.fs_repository.directory_exists(mount_path):
                self.fs_repository.create_directory(mount_path)
        except Exception as e:
            raise MountException(f"Error adding mount point {mount_path}: {e}")

    def _validate_mount_point(self, mount_path: str):
        """
        Validate that is the mount point exists, it needs to be empty
        :param mount_path: The path to validate
        """

        # Check the mount point exists and if it is empty
        if self.fs_repository.directory_exists(mount_path) and not self.fs_repository.directory_empty(mount_path):
            raise UnmountException(
                f"Mount point {mount_path} is not empty, please remove the contents before unmounting"
            )
