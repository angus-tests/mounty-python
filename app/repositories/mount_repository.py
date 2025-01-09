import json
import os
import subprocess
from abc import ABC, abstractmethod


from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.factories.mount_factory import MountFactory
from app.models.mount import Mount
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


class MountRepository(MountRepositoryInterface):
    """
    Concrete implementation of a mount repository
    """

    def __init__(self,
                 config_manager: ConfigManager,
                 mount_config_repository: MountConfigRepository,
                 mount_prefix="/shares"):
        self.config_manager = config_manager
        self.mount_config_repository = mount_config_repository
        self.mount_prefix = mount_prefix

    def get_current_mounts(self) -> list[Mount]:
        """
        Get all the mounts on the system that we are interested in
        these are the ones that are prefixed with self.mount_prefix
        """

        # Fetch all the mounts on the system from the config repo
        all_system_mounts = self.mount_config_repository.get_all_system_mounts()

        # Filter out the mounts that don't start with our mount prefix
        return [
            mount
            for mount in all_system_mounts
            if mount.mount_path.startswith(self.mount_prefix)
        ]

    def get_desired_mounts(self) -> list[Mount]:
        """
        Read in the desired mounts from a .json file
        """

        with open(self.config_manager.get_config("DESIRED_MOUNTS_FILE"), "r") as f:
            mounts_data = json.load(f)

        mounts = [
            MountFactory.create_from_json(mount)
            for mount in mounts_data
        ]

        return mounts

    def mount(self, mount: Mount):
        """
        Add a mount to the system
        """

        # Create the mount point if it doesn't exist
        if not os.path.exists(f"{mount.mount_path}"):
            os.makedirs(mount.mount_path, exist_ok=True)

        # Store this mount information on the system to persist
        self.mount_config_repository.store_mount_information(mount)

        # Call the mount command
        result = subprocess.run(["sudo", "mount", mount.mount_path], capture_output=True)

        # Check if the mount was successful
        if result.returncode != 0:
            raise MountException(result.stderr)

    def unmount(self, mount_path: str):
        """
        Remove a mount from the system
        :param mount_path: The local path of the mount to unmount
        """

        # Remove from fstab
        self.mount_config_repository.remove_mount_information(mount_path)

        # Perform unmount
        umount_result = subprocess.run(["umount", mount_path])

        # Check if the unmount was successful
        if umount_result.returncode != 0:
            raise UnmountException(f"Error unmounting - {umount_result.stderr}")
        else:
            # Remove the mount point (only if unmount success)
            rm_result = subprocess.run(["rm", "-rf", mount_path])

            if rm_result.returncode != 0:
                raise UnmountException(f"Error removing mount point - {rm_result.stderr}")

    def unmount_all(self):
        """
        Unmount all mounts from the system
        that start with our mount prefix and keep the rest
        """

        # Get all our mounts
        all_mounts = self.get_current_mounts()

        # Remove these mounts from the system
        self.mount_config_repository.remove_mounts(all_mounts)

        # Store the failed mounts
        failed_to_unmount = []

        # Go through each mount and unmount
        for mount in all_mounts:
            umount_result = subprocess.run(["umount", mount.mount_path])
            if umount_result.returncode != 0:
                failed_to_unmount.append(mount)
            else:
                rm_result = subprocess.run(["rm", "-rf", mount.mount_path])
                if rm_result.returncode != 0:
                    failed_to_unmount.append(mount)

        # Return a list of failed mounts
        return failed_to_unmount


