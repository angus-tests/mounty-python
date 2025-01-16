import re
import unittest
from unittest.mock import MagicMock, mock_open, patch

from app.exceptions.mount_exception import MountException
from app.factories.mount_factory import FakeMountFactory
from app.repositories.file_sytem_repository import FileSystemRepositoryInterface
from app.repositories.mount_config_repository import FstabRepository
from app.util.config import ConfigManager


class TestHelper:

    default_config_values = {
        "FSTAB_LOCATION": "/etc/fstab",
        "PROC_MOUNTS_LOCATION": "/proc/mounts",
        "CIFS_FILE_LOCATION": "/etc/.cifs",
        "LINUX_SSH_LOCATION": "/root/.ssh/id_rsa_linux",
        "LINUX_SSH_USER": "dave",
        "CIFS_DOMAIN": "ONS"
    }

    @staticmethod
    def setup_mock_fstab_repository(fstab_content: str = "", config_values=None):
        """
        Sets up the common mocked FSTAB repository and configuration manager.
        """

        # If no config values are provided, use the default values
        if config_values is None:
            config_values = TestHelper.default_config_values

        # Create a mock file system repository
        mock_fs_repository = MagicMock(spec=FileSystemRepositoryInterface)

        # Create a side effect for the read_file method
        def read_file_side_effect(file_path):
            if file_path == config_values["FSTAB_LOCATION"]:
                return fstab_content
            elif file_path == config_values["PROC_MOUNTS_LOCATION"]:
                return fstab_content
            return ""

        # Set the side effect for the read_file method
        mock_fs_repository.read_file.side_effect = read_file_side_effect

        # Mock a config manager
        mock_config_manager = MagicMock(spec=ConfigManager)

        # Use a lambda to return values based on the parameter
        mock_config_manager.get_config.side_effect = lambda key: config_values[key]

        # Create a fstab repository
        return FstabRepository(mock_config_manager, mock_fs_repository)

    @staticmethod
    def format_line(content):
        """
        Remove all spaces and special characters from the content
        """
        return re.sub(r"\s+", "", content)

    @staticmethod
    def compare_file_contents(expected_content, actual_content):
        """
        Compare the contents of two files, ignoring order and whitespace
        """
        expected_lines = expected_content.split("\n")
        actual_lines = actual_content.split("\n")

        # Remove any empty lines and remove spaces and special characters
        expected_lines = [TestHelper.format_line(line) for line in expected_lines if line.strip()]
        actual_lines = [TestHelper.format_line(line) for line in actual_lines if line.strip()]

        # Assert two lists are equal (ignoring order)
        return sorted(expected_lines) == sorted(actual_lines)


class TestStoreMountInformation(unittest.TestCase):

    def test_store_mount_information_windows_success(self):
        """
        This test will simulate storing mounting information for a windows mount
        in the fstab file
        """

        cifs_file_location = TestHelper.default_config_values["CIFS_FILE_LOCATION"]
        ssh_file_location = TestHelper.default_config_values["LINUX_SSH_LOCATION"]
        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        # Mock the FSTAB content
        fstab_content = f"""
        /mnt/windows /system/mounts/windows cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
        {ssh_user}@/mnt/linux /system/mounts/linux fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
        """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create our mount
        mount = FakeMountFactory.windows_mount(
            mount_path="/shares/windows",
            actual_path="/mnt/windows/folder"
        )

        # Run the store the mount information method
        fstab_repository.store_mount_information(mount)

        # Assert the content was written correctly
        expected_content = f"""
        /mnt/windows /system/mounts/windows cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
        {ssh_user}@/mnt/linux /system/mounts/linux  fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
        /mnt/windows/folder /shares/windows cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
        """

        # Assert the content was written correctly
        actual = fstab_repository.fs_repository.write_file.call_args[0][1]
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

    def test_store_mount_information_linux_success(self):
        """
        This test will simulate storing mounting information for a linux mount
        in the fstab file
        """

        cifs_file_location = TestHelper.default_config_values["CIFS_FILE_LOCATION"]
        ssh_file_location = TestHelper.default_config_values["LINUX_SSH_LOCATION"]
        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]
        cifs_domain = TestHelper.default_config_values["CIFS_DOMAIN"]

        # Mock the FSTAB content
        fstab_content = f"""
                /mnt/windows /shares/windows1 cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0
                {ssh_user}@/mnt/linux /shares/linux1 fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
                """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create our mount
        mount = FakeMountFactory.linux_mount(
            mount_path="/shares/linux2",
            actual_path=f"{ssh_user}@/linuxserver/mount"
        )

        # Run the store the mount information method
        fstab_repository.store_mount_information(mount)

        # Assert the content was written correctly
        expected_content = f"""
                /mnt/windows /shares/windows1 cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
                {ssh_user}@/mnt/linux /shares/linux1  fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
                {ssh_user}@/linuxserver/mount /shares/linux2  fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
                """

        # Assert the content was written correctly
        actual = fstab_repository.fs_repository.write_file.call_args[0][1]
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

    def test_store_mount_information_unsupported_mount_type(self):
        """
        This test will simulate storing mounting information for an unsupported mount
        in the fstab file
        """

        fstab_repository = TestHelper.setup_mock_fstab_repository()

        # Create our mount
        mount = FakeMountFactory.standard_mount()

        # Assert a MountException is raised
        with self.assertRaises(MountException):
            # Run the store the mount information method
            fstab_repository.store_mount_information(mount)

    def test_store_mount_removes_duplicates(self):
        """
        This test will simulate an fstab with duplicate entries
        and ensure that the duplicates are removed when storing a new mount
        """

        cifs_file_location = TestHelper.default_config_values["CIFS_FILE_LOCATION"]
        ssh_file_location = TestHelper.default_config_values["LINUX_SSH_LOCATION"]
        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]
        cifs_domain = TestHelper.default_config_values["CIFS_DOMAIN"]

        # Mock the FSTAB content (include duplicates)
        fstab_content = f"""
            /mnt/windows /shares/windows1 cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0
            {ssh_user}@/mnt/linux /shares/linux1 fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
            /mnt/windows /shares/windows1 cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create our mount
        mount = FakeMountFactory.linux_mount(
            mount_path="/shares/windows2",
            actual_path=f"/mnt/windows2"
        )

        # Run the store the mount information method
        fstab_repository.store_mount_information(mount)

        # Assert the content was written correctly
        expected_content = f"""
                /mnt/windows /shares/windows1 cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
                {ssh_user}@/mnt/linux /shares/linux1  fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
                /mnt/windows2 /shares/windows2 cifs credentials={cifs_file_location},domain=ONS,uid=1001,gid=5001,auto 0 0
                """

        # Assert the content was written correctly
        actual = fstab_repository.fs_repository.write_file.call_args[0][1]
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

class TestRemoveMountInformation(unittest.TestCase):

    def test_remove_mount_information_windows_success(self):
        """
        This test will simulate removing mounting information for a windows mount
        """

        cifs_file_location = TestHelper.default_config_values["CIFS_FILE_LOCATION"]
        cifs_domain = TestHelper.default_config_values["CIFS_DOMAIN"]

        # Mock the FSTAB content
        fstab_content = f"""
        /mnt/windowserver1 /shares/windows1 cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0
        /mnt/windowserver2 /shares/windows2 cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0
        """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create a mount that already exists in the fstab file
        mount = FakeMountFactory.windows_mount(
            mount_path="/shares/windows1",
            actual_path="/mnt/windowserver1"
        )

        # Run the store the mount information method
        fstab_repository.remove_mount_information(mount.mount_path)

        # Assert the content was written correctly
        expected_content = f"""
        /mnt/windowserver2 /shares/windows2 cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0
        """

        # Assert the content was written correctly
        actual = fstab_repository.fs_repository.write_file.call_args[0][1]
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

    def test_remove_mount_information_linux_success(self):
        """
        This test will simulate removing mounting information for a linux mount
        """

        ssh_file_location = TestHelper.default_config_values["LINUX_SSH_LOCATION"]
        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        # Mock the FSTAB content
        fstab_content = f"""
        {ssh_user}@/mnt/linuxserver1 /shares/linux1 fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
        {ssh_user}@/mnt/linuxserver2 /shares/linux2 fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
        """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create a mount that already exists in the fstab file
        mount = FakeMountFactory.linux_mount(
            mount_path="/shares/linux1",
            actual_path=f"{ssh_user}@/mnt/linuxserver1"
        )

        # Run the store the mount information method
        fstab_repository.remove_mount_information(mount.mount_path)

        # Assert the content was written correctly
        expected_content = f"""
        {ssh_user}@/mnt/linuxserver2 /shares/linux2 fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0
        """

        # Assert the content was written correctly
        actual = fstab_repository.fs_repository.write_file.call_args[0][1]
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )


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
