import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod


from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.facades.log_facade import LogFacade
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

        current_mounts = []

        # Filter out the mounts that don't start with our mount prefix
        for mount in all_system_mounts:
            if mount.mount_path.startswith(self.mount_prefix) and os.path.ismount(mount.mount_path):
                current_mounts.append(mount)
            elif not os.path.ismount(mount.mount_path) and mount.mount_path.startswith(self.mount_prefix):
                LogFacade.warning(f"Mount {mount.mount_path} is present in the config but not mounted on the system")

        return current_mounts

    def get_desired_mounts(self) -> list[Mount]:
        """
        Read in the desired mounts from a .json file
        """

        with open(self.config_manager.get_config("DESIRED_MOUNTS_FILE_PATH"), "r") as f:
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

        # TODO abstract FS operations to another class
        # Create the mount point if it doesn't exist
        if not os.path.exists(f"{mount.mount_path}"):
            os.makedirs(mount.mount_path, exist_ok=True)

        # Store this mount information on the system to persist
        self.mount_config_repository.store_mount_information(mount)

        # Call the mount command
        result = subprocess.run(["sudo", "mount", mount.mount_path], capture_output=True)

        # Check if the mount was successful
        if result.returncode != 0:

            # Check if the mount was not successful
            if not os.path.ismount(mount.mount_path):
                LogFacade.warning(f"Mount operation failed removing mount information for {mount.mount_path}")

            # Raise an exception
            raise MountException(result.stderr)

    def unmount(self, mount_path: str):
        """
        Remove a mount from the system
        :param mount_path: The local path of the mount to unmount
        """

        # Remove from fstab
        self.mount_config_repository.remove_mount_information(mount_path)

        if not os.path.ismount(mount_path):
            LogFacade.warning(f"Attempted to unmount {mount_path} but it was already unmounted")
            return

        # Perform unmount
        umount_result = subprocess.run(["umount", mount_path])

        # Check if the unmount was successful
        if umount_result.returncode != 0:

            # Check if this was a "not mounted" error which means it was already unmounted
            if "not mounted." in umount_result.stderr.decode("utf-8"):
                LogFacade.warning(f"Attempted to unmount {mount_path} but it was already unmounted")
            else:
                raise UnmountException(f"Error unmounting - {umount_result.stderr}")

        # TODO abstract shutil operations to another class
        # Remove the mount point
        try:
            shutil.rmtree(mount_path)
        except Exception as e:
            raise UnmountException(f"Error removing mount point - {e}")

    def unmount_all(self):
        """
        Unmount all mounts from the system
        that start with our mount prefix and keep the rest
        """

        # TODO test this method

        # Get all our mounts
        all_mounts = self.get_current_mounts()

        # Remove these mounts from the system
        self.mount_config_repository.remove_mounts(all_mounts)

        # Store the failed mounts
        failed_to_unmount = []

        # TODO clean up this code

        # Go through each mount and unmount
        for mount in all_mounts:
            umount_result = subprocess.run(["umount", mount.mount_path])
            if umount_result.returncode != 0:

                if not os.path.ismount(mount.mount_path):
                    LogFacade.warning(f"Attempted to unmount {mount.mount_path} but it was already unmounted")
                    try:
                        shutil.rmtree(mount.mount_path)
                    except Exception:
                        LogFacade.error(f"Failed to remove mount point {mount.mount_path}")
                        failed_to_unmount.append(mount)
                else:
                    failed_to_unmount.append(mount)
            else:
                try:
                    shutil.rmtree(mount.mount_path)
                except Exception:
                    LogFacade.error(f"Failed to remove mount point {mount.mount_path}")
                    failed_to_unmount.append(mount)
                LogFacade.info(f"Unmounted {mount.mount_path} successfully")

        # Return a list of failed mounts
        return failed_to_unmount


