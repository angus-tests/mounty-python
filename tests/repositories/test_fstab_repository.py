import re
import unittest
from unittest.mock import MagicMock, mock_open, patch

from app.exceptions.mount_exception import MountException
from app.factories.mount_factory import FakeMountFactory
from app.repositories.mount_config_repository import FstabRepository
from app.util.config import ConfigManager


def format_file_contents(content):
    """
    Remove all spaces and special characters from the content
    """
    return re.sub(r"\s+", "", content)


class TestStoreMountInformation(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open)
    def test_store_mount_information_windows_success(self, mock_fstab_open):
        """
        This test will simulate storing mounting information for a windows mount
        in the fstab file
        """

        cifs_file_location = "/etc/.cifs"

        # Mock the FSTAB content
        mock_fstab_open.return_value.read.return_value = f"""
        /mnt/windows /system/mounts/windows cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
        ben@/mnt/linux /system/mounts/linux fuse.sshfs IdentityFile=/path/to/.ssh/id_rsa_linux,uid=1001,gid=5001,auto 0 0
        """

        # Create our mount
        mount = FakeMountFactory.windows_mount(
            mount_path="/shares/windows",
            actual_path="/mnt/windows/folder"
        )

        mock_config_manager = MagicMock(spec=ConfigManager)

        # Mock the cifs_file_location
        mock_config_manager.get_config.return_value = cifs_file_location

        # Create a fstab repository
        fstab_repository = FstabRepository(mock_config_manager)

        # Store the mount information
        fstab_repository.store_mount_information(mount)

        # Assert the content was written correctly
        expected_content = f"""
        /mnt/windows /system/mounts/windows cifs credentials=/etc/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        ben@/mnt/linux /system/mounts/linux  fuse.sshfs IdentityFile=/path/to/.ssh/id_rsa_linux,uid=1001,gid=5001,auto 0 0
        /mnt/windows/folder /shares/windows cifs credentials=/etc/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        """

        # Format the expected and actual to make them comparable
        expected_formatted = format_file_contents(expected_content)
        actual_content = mock_fstab_open().write.call_args[0][0]
        actual_formatted = format_file_contents(actual_content)

        # Assert the content was written correctly
        self.assertEqual(expected_formatted, actual_formatted)

    @patch("builtins.open", new_callable=mock_open)
    def test_store_mount_information_linux_success(self, mock_fstab_open):
        """
        This test will simulate storing mounting information for a linux mount
        in the fstab file
        """

        linux_user = "dave"
        linux_ssh_location = "/root/.ssh/id_rsa_linux"

        # Mock the FSTAB content
        mock_fstab_open.return_value.read.return_value = f"""
        /mnt/windows /system/mounts/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        {linux_user}@/mnt/linux /system/mounts/linux fuse.sshfs IdentityFile={linux_ssh_location},uid=1001,gid=5001 0 0
        """

        # Create our mount
        mount = FakeMountFactory.linux_mount(
            mount_path="/shares/linux",
            actual_path=f"{linux_user}@/mnt/linux/new"
        )

        mock_config_manager = MagicMock(spec=ConfigManager)

        # Mock the cifs_file_location
        config_values = {
            "LINUX_SSH_LOCATION": linux_ssh_location,
            "LINUX_SSH_USER": linux_user,
            "FSTAB_LOCATION": "/etc/fstab",
            "PROC_MOUNTS_LOCATION": "/proc/mounts"
        }

        # Use a lambda to return values based on the parameter
        mock_config_manager.get_config.side_effect = lambda key: config_values[key]

        # Create a fstab repository
        fstab_repository = FstabRepository(mock_config_manager)

        # Store the mount information
        fstab_repository.store_mount_information(mount)

        # Assert the content was written correctly
        expected_content = f"""
        /mnt/windows /system/mounts/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        {linux_user}@/mnt/linux /system/mounts/linux fuse.sshfs IdentityFile={linux_ssh_location},uid=1001,gid=5001 0 0
        {linux_user}@/mnt/linux/new /shares/linux fuse.sshfs IdentityFile={linux_ssh_location},uid=1001,gid=5001,auto 0 0
        """

        # Format the expected and actual to make them comparable
        expected_formatted = format_file_contents(expected_content)
        actual_content = mock_fstab_open().write.call_args[0][0]
        actual_formatted = format_file_contents(actual_content)

        # Assert the content was written correctly
        self.assertEqual(expected_formatted, actual_formatted)

    def test_store_mount_information_unsupported_mount_type(self):
        """
        This test will simulate storing mounting information for an unsupported mount
        in the fstab file
        """

        # Create our mount
        mount = FakeMountFactory.standard_mount()

        mock_config_manager = MagicMock(spec=ConfigManager)

        # Create a fstab repository
        fstab_repository = FstabRepository(mock_config_manager)

        # Store the mount information
        with self.assertRaises(MountException):
            fstab_repository.store_mount_information(mount)


class TestRemoveMountInformation(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open)
    def test_remove_mount_information_windows_success(self, mock_fstab_open):
        """
        This test will simulate removing mounting information for a windows mount
        from the fstab file
        """

        # Mock the FSTAB content
        mock_fstab_open.return_value.read.return_value = f"""
        /mnt/windows /system/mounts/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        /mnt/windows/folder /shares/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        """

        # Create a mount that exists in the fstab file
        mount = FakeMountFactory.windows_mount(
            mount_path="/shares/windows",
            actual_path="/mnt/windows/folder"
        )

        mock_config_manager = MagicMock(spec=ConfigManager)

        # Create the fstab repository
        fstab_repository = FstabRepository(mock_config_manager)

        # Remove the mount information
        fstab_repository.remove_mount_information(mount.mount_path)

        # Ensure that the mount information was removed when it is written back to the file

        expected_content = f"""
        /mnt/windows /system/mounts/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
        """

        # Format the expected and actual to make them comparable
        expected_formatted = format_file_contents(expected_content)
        actual_content = mock_fstab_open().write.call_args[0][0]
        actual_formatted = format_file_contents(actual_content)

        # Assert the content was written correctly
        self.assertEqual(expected_formatted, actual_formatted)


class TestRemoveMounts(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open)
    def test_remove_multiple_mounts(self, mock_fstab_open):
        """
        This test will simulate removing multiple mounts from the fstab file
        """

        # Mock the FSTAB content
        mock_fstab_open.return_value.read.return_value = f"""
                /mnt/windows /system/mounts/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
                /mnt/windows/folder /shares/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
                /mnt/linux /shares/linux/mount fuse.sshfs IdentityFile=/path/to/.ssh/id_rsa_linux,uid=1001,gid=5001,auto 0 0
                """

        # Create a list of mounts that exist in the fstab file
        mounts = [
            FakeMountFactory.windows_mount(
                mount_path="/shares/windows",
                actual_path="/mnt/windows/folder"
            ),
            FakeMountFactory.linux_mount(
                mount_path="/shares/linux/mount",
                actual_path="/mnt/linux"
            )
        ]

        mock_config_manager = MagicMock(spec=ConfigManager)

        # Create the fstab repository
        fstab_repository = FstabRepository(mock_config_manager)

        # Remove the mounts
        fstab_repository.remove_mounts(mounts)

        # Ensure that the mount information was removed when it is written back to the file

        expected_content = f"""
                /mnt/windows /system/mounts/windows cifs credentials=/path/to/.cifs,domain=ONS,uid=1001,gid=5001,auto 0 0
                """

        # Format the expected and actual to make them comparable
        expected_formatted = format_file_contents(expected_content)
        actual_content = mock_fstab_open().write.call_args[0][0]
        actual_formatted = format_file_contents(actual_content)

        # Assert the content was written correctly
        self.assertEqual(expected_formatted, actual_formatted)


if __name__ == '__main__':
    unittest.main()
