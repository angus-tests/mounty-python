from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.facades.log_facade import LogFacade
from app.models.mount import Mount
from app.repositories.mount_repository import MountRepositoryInterface


class MountingService:

    def __init__(self, mount_repository: MountRepositoryInterface):
        self.mount_repository = mount_repository

    def run(self):
        """
        Run the mounting service
        """

        # Fetch the desired mounts from the repository
        desired_mounts = self.mount_repository.get_desired_mounts()

        # Fetch the current mounts from the repository
        current_mounts = self.mount_repository.get_current_mounts()

        # Find mounts to add
        mounts_to_add = self._find_mounts_to_add(desired_mounts, current_mounts)

        # Find mounts to remove
        mounts_to_remove = self._find_mounts_to_remove(desired_mounts, current_mounts)

        # Find mounts to update
        mounts_to_update = self._find_mounts_to_update(desired_mounts, current_mounts)

        # Log any failed mounts

        # Return status
        pass

    def _mount(self, mount: Mount):
        """
        Mount a directory
        """
        LogFacade.info(f"Mounting {mount.mount_path} -> {mount.actual_path}")
        try:
            self.mount_repository.mount(mount)
        except MountException as e:
            LogFacade.error(f"Failed to mount {mount.mount_path} -> {mount.actual_path}: {e}")

    def _unmount(self, mount: Mount):
        """
        Unmount a directory
        """
        LogFacade.info(f"Unmounting {mount.mount_path}")
        try:
            self.mount_repository.unmount(mount)
        except UnmountException as e:
            LogFacade.error(f"Failed to unmount {mount.mount_path}: {e}")

    def _find_mounts_to_remove(self, desired_mounts: list[Mount], current_mounts: list[Mount]) -> list[Mount]:
        """
        Look for mounts on the system we can remove
        """

        # Make a list of the local mount paths for the desired mounts
        desired_mount_paths = [mount.mount_path for mount in desired_mounts]

        # Make a list of the local mount paths for the current mounts
        current_mount_paths = [mount.mount_path for mount in current_mounts]

        # Any mounts that are in the current mounts but not in the desired mounts can be removed
        return [mount for mount in current_mount_paths if mount not in desired_mount_paths]

    def _find_mounts_to_add(self, desired_mounts: list[Mount], current_mounts: list[Mount]) -> list[Mount]:
        """
        Look for mounts we need to add
        """

        # Make a list of the local mount paths for the desired mounts
        desired_mount_paths = [mount.mount_path for mount in desired_mounts]

        # Make a list of the local mount paths for the current mounts
        current_mount_paths = [mount.mount_path for mount in current_mounts]

        # Any mounts that are in the desired mounts but not in the current mounts can be added
        return [mount for mount in desired_mount_paths if mount not in current_mount_paths]

    def _find_mounts_to_update(self, desired_mounts: list[Mount], current_mounts: list[Mount]) -> list[Mount]:
        """
        Look for mounts we need to update
        """

        # Make a list of the local mount paths for the desired mounts
        desired_mount_paths = [mount.mount_path for mount in desired_mounts]

        # Make a list of the local mount paths for the current mounts
        current_mount_paths = [mount.mount_path for mount in current_mounts]

        # Any mounts that are in both the desired mounts and the current mounts can be updated
        return [mount for mount in desired_mount_paths if mount in current_mount_paths]