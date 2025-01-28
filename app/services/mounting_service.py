from collections.abc import Callable

from app.exceptions.cleanup_exception import CleanupException
from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.facades.log_facade import LogFacade
from app.models.mount import Mount
from app.interfaces.mount_repository_interface import MountRepositoryInterface


class MountingService:

    def __init__(self, mount_repository: MountRepositoryInterface):
        self.mount_repository = mount_repository

    def run(self) -> bool:
        """
        Run the mounting service by adding, removing, and updating mounts as needed.
        """
        desired_mounts, current_mounts = self._fetch_mount_data()

        # Process mounts
        all_operations_successful = (
            self._process_mounts("add", desired_mounts, current_mounts, self._add_mounts) and
            self._process_mounts("remove", desired_mounts, current_mounts, self._remove_mounts) and
            self._process_mounts("update", desired_mounts, current_mounts, self._update_mounts)
        )

        return all_operations_successful

    def dry_run(self) -> bool:
        """
        Display the mounts that would be added, removed, or updated without making any changes.
        """
        desired_mounts, current_mounts = self._fetch_mount_data()
        orphan_mounts = self.mount_repository.get_orphan_mounts()

        # Log planned operations
        self._log_mounts("add", desired_mounts, current_mounts)
        self._log_mounts("remove", desired_mounts, current_mounts)
        self._log_mounts("update", desired_mounts, current_mounts)
        self._log_mounts("orphans", desired_mounts, current_mounts, orphan_mounts, custom_message="Orphan mounts")
        self._log_mounts("current", desired_mounts, current_mounts, custom_message="Current mounts")

        return True

    def cleanup(self) -> bool:
        """
        Cleanup the fstab file
        :return True if the cleanup was successful
        """
        LogFacade.info("Cleanup running...")
        try:
            self.mount_repository.cleanup()
        except CleanupException as e:
            LogFacade.error(f"Failed to cleanup mounts: {e}")
            return False
        return True

    def unmount_all(self) -> bool:
        """
        Unmount all mounts from the system
        :return True if all mounts were unmounted successfully
        """
        LogFacade.info("Unmounting all mounts...")
        failed_to_umount = self.mount_repository.unmount_all()

        # If at least one mount failed, log the results
        if failed_to_umount:
            LogFacade.log_table_error(
                "Failed to unmount these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_to_umount])

        # Return status (at least once failed mount is a failure)
        return len(failed_to_umount) == 0

    def _fetch_mount_data(self):
        """
        Fetch desired and current mounts from the repository.
        """
        desired_mounts = self.mount_repository.get_desired_mounts()
        current_mounts = self.mount_repository.get_current_mounts()
        return desired_mounts, current_mounts

    def _process_mounts(self, action: str,
                        desired_mounts: list[Mount],
                        current_mounts: list[Mount],
                        operation: Callable) -> bool:
        """
        Process mounts for a specific action (add, remove, update) using the provided operation.
        """
        if action == "add":
            mounts = self._find_mounts_to_add(desired_mounts, current_mounts)
        elif action == "remove":
            mounts = self._find_mounts_to_remove(desired_mounts, current_mounts)
        elif action == "update":
            mounts = self._find_mounts_to_update(desired_mounts, current_mounts)
        else:
            raise ValueError(f"Unknown action: {action}")

        # Log the mounts that will be processed
        self._log_mounts(action, desired_mounts, current_mounts)

        # Perform the operation and return the result
        return operation(mounts)

    def _log_mounts(self, action: str,
                    desired_mounts: list[Mount],
                    current_mounts: list[Mount],
                    orphan_mounts=None,
                    custom_message=None):
        """
        Log mount actions (add, remove, update) to provide an overview of planned operations.
        """
        if action == "add":
            mounts = self._find_mounts_to_add(desired_mounts, current_mounts)
        elif action == "remove":
            mounts = self._find_mounts_to_remove(desired_mounts, current_mounts)
        elif action == "update":
            mounts = self._find_mounts_to_update(desired_mounts, current_mounts)
        elif action == "orphans":
            mounts = orphan_mounts
        elif action == "current":
            mounts = current_mounts
        else:
            raise ValueError(f"Unknown action: {action}")

        title = f"Mounts to {action}" if custom_message is None else custom_message

        LogFacade.log_table_info(
            title,
            ["Mount Path", "Actual Path"],
            [[mount.mount_path, mount.actual_path] for mount in mounts]
        )

    def _mount(self, mount: Mount) -> bool:
        """
        Mount a directory
        :return True if the mount was mounted successfully
        """
        LogFacade.info(f"Mounting {mount.mount_path} -> {mount.actual_path} ...")
        try:
            self.mount_repository.mount(mount)
        except MountException as e:
            LogFacade.error(f"Failed to mount {mount.mount_path} -> {mount.actual_path}: {e}")
            return False
        return True

    def _unmount(self, mount: Mount) -> bool:
        """
        Unmount a directory
        :return True if the mount was unmounted successfully
        """
        LogFacade.info(f"Unmounting {mount.mount_path} ...")
        try:
            self.mount_repository.unmount(mount.mount_path)
        except UnmountException as e:
            LogFacade.error(f"Failed to unmount {mount.mount_path}: {e}")
            return False
        return True

    def _remove_mounts(self, mounts: list[Mount]) -> bool:
        """
        Remove a list of mounts from the system
        :return: True if all mounts were removed successfully
        """
        failed_mounts = []
        success_mounts = []
        for mount in mounts:
            if not self._unmount(mount):
                failed_mounts.append(mount)
            else:
                success_mounts.append(mount)

        # Log the unsuccessful mounts
        if failed_mounts:
            LogFacade.log_table_error(
                "Failed to remove these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_mounts])

        # Log the successful mounts
        if success_mounts:
            LogFacade.log_table_info(
                "Successfully removed these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in success_mounts])

        return len(failed_mounts) == 0

    def _add_mounts(self, mounts: list[Mount]) -> bool:
        """
        Add a list of mounts to the system
        :return: True if all mounts were added successfully
        """
        failed_mounts = []
        success_mounts = []
        for mount in mounts:
            if not self._mount(mount):
                failed_mounts.append(mount)
            else:
                success_mounts.append(mount)

        # Log the unsuccessful mounts
        if failed_mounts:
            LogFacade.log_table_error(
                "Failed to add these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_mounts])

        # Log the successful mounts
        if success_mounts:
            LogFacade.log_table_info(
                "Successfully added these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in success_mounts])
        return len(failed_mounts) == 0

    def _update_mounts(self, mounts: list[Mount]) -> bool:
        """
        Update a list of mounts
        :return: True if all mounts were updated successfully
        """
        failed_mounts = []
        success_mounts = []
        for mount in mounts:
            if not self._unmount(mount) or not self._mount(mount):
                failed_mounts.append(mount)
            else:
                success_mounts.append(mount)

        # Log the unsuccessful mounts
        if failed_mounts:
            LogFacade.log_table_error(
                "Failed to update these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in failed_mounts])

        # Log the successful mounts
        if success_mounts:
            LogFacade.log_table_info(
                "Successfully updated these mounts",
                ["Mount Path", "Actual Path"],
                [[mount.mount_path, mount.actual_path] for mount in success_mounts])
        return len(failed_mounts) == 0

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
                # If the mount paths are the same but the mounts are different then we need to update
                if (desired_mount.mount_path == current_mount.mount_path
                        and desired_mount != current_mount):
                    mounts_to_update.append(desired_mount)
        return mounts_to_update
