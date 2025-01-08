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
        LogFacade.log_table_info(
            "Mounts to add",
            ["Mount Path", "Actual Path"],
            [[mount.mount_path, mount.actual_path] for mount in mounts_to_add])
        failed_to_add = self._add_mounts(mounts_to_add)

        # Find mounts to remove
        mounts_to_remove = self._find_mounts_to_remove(desired_mounts, current_mounts)
        LogFacade.log_table_info(
            "Mounts to remove",
            ["Mount Path", "Actual Path"],
            [[mount.mount_path, mount.actual_path] for mount in mounts_to_remove])
        failed_to_remove = self._remove_mounts(mounts_to_remove)

        # Find mounts to update
        mounts_to_update = self._find_mounts_to_update(desired_mounts, current_mounts)
        LogFacade.log_table_info(
            "Mounts to update",
            ["Mount Path", "Actual Path"],
            [[mount.mount_path, mount.actual_path] for mount in mounts_to_update])
        failed_to_update = self._update_mounts(mounts_to_update)

        # Log any failed mounts
        if failed_to_add:
            LogFacade.log_table_error(
                "Failed to add these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_to_add])

        if failed_to_remove:
            LogFacade.log_table_error(
                "Failed to remove these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_to_remove])

        if failed_to_update:
            LogFacade.log_table_error(
                "Failed to update these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_to_update])

        # Return status (True if all mounts were successful)
        return not failed_to_add and not failed_to_remove and not failed_to_update

    def unmount_all(self) -> bool:
        """
        Unmount all mounts from the system
        """
        LogFacade.info("Unmounting all mounts")
        try:
            self.mount_repository.unmount_all()
        except UnmountException as e:
            LogFacade.error(f"Failed to unmount all mounts: {e}")
            return False
        return True

    def _mount(self, mount: Mount) -> bool:
        """
        Mount a directory
        """
        LogFacade.info(f"Mounting {mount.mount_path} -> {mount.actual_path}")
        try:
            self.mount_repository.mount(mount)
        except MountException as e:
            LogFacade.error(f"Failed to mount {mount.mount_path} -> {mount.actual_path}: {e}")
            return False
        return True

    def _unmount(self, mount: Mount) -> bool:
        """
        Unmount a directory
        """
        LogFacade.info(f"Unmounting {mount.mount_path}")
        try:
            self.mount_repository.unmount(mount.mount_path)
        except UnmountException as e:
            LogFacade.error(f"Failed to unmount {mount.mount_path}: {e}")
            return False
        return True

    def _update_mount(self, mount: Mount) -> bool:
        """
        Update an existing mount
        this will use the mount path to remove the mount,
        then remount the mount with the new details
        """
        LogFacade.info(
            f"Updating {mount.mount_path}")
        try:
            self.mount_repository.unmount(mount.mount_path)
            self.mount_repository.mount(mount)
        except (MountException, UnmountException) as e:
            LogFacade.error(
                f"Failed to update {mount.mount_path}: {e}")
            return False
        return True

    def _remove_mounts(self, mounts: list[Mount]) -> list[Mount]:
        """
        Remove a list of mounts from the system
        :return: A list of mounts that failed to be removed
        """
        failed_mounts = []
        for mount in mounts:
            if not self._unmount(mount):
                failed_mounts.append(mount)
        return failed_mounts

    def _add_mounts(self, mounts: list[Mount]) -> list[Mount]:
        """
        Add a list of mounts to the system
        :return: A list of mounts that failed to be added
        """
        failed_mounts = []
        for mount in mounts:
            if not self._mount(mount):
                failed_mounts.append(mount)
        return failed_mounts

    def _update_mounts(self, mounts: list[Mount]) -> list[Mount]:
        """
        Update a list of mounts
        :return: A list of mounts that failed to be updated
        """
        failed_mounts = []
        for mount in mounts:
            if not self._unmount(mount) or not self._mount(mount):
                failed_mounts.append(mount)
        return failed_mounts

    def _find_mounts_to_remove(self, desired_mounts: list[Mount], current_mounts: list[Mount]) -> list[Mount]:
        """
        Look for mounts on the system we can remove
        A mount is considered to be removable if it is not in the desired mounts
        but is in the current mounts
        """

        # Make a list of the local mount paths for the desired mounts
        desired_mount_paths = [mount.mount_path for mount in desired_mounts]

        # Any mounts that are in the current mounts but not in the desired mounts can be removed
        return [mount for mount in current_mounts if mount.mount_path not in desired_mount_paths]

    def _find_mounts_to_add(self, desired_mounts: list[Mount], current_mounts: list[Mount]) -> list[Mount]:
        """
        Look for mounts we need to add
        A mount is considered to need adding if the mount path is
        not in the current mounts
        """

        # Make a list of the local mount paths for the current mounts
        current_mount_paths = [mount.mount_path for mount in current_mounts]

        # Any mounts that are in the desired mounts but not in the current mounts can be added
        return [mount for mount in desired_mounts if mount.mount_path not in current_mount_paths]

    def _find_mounts_to_update(self, desired_mounts: list[Mount], current_mounts: list[Mount]) -> list[Mount]:
        """
        Look for mounts we need to update
        A mount is considered to need updating if the mount path is
        the same but the actual path or mount type is different
        """

        mounts_to_update = []

        for desired_mount in desired_mounts:
            for current_mount in current_mounts:
                if desired_mount.mount_path == current_mount.mount_path and (desired_mount.actual_path != current_mount.actual_path or desired_mount.mount_type != current_mount.mount_type):
                    mounts_to_update.append(desired_mount)
        return mounts_to_update
