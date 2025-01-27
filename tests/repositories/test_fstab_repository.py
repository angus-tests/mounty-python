import re
import unittest
from unittest.mock import MagicMock, mock_open, patch

from app.enums.enums import MountType
from app.exceptions.mount_exception import MountException
from app.factories.fake_mount_factory import FakeMountFactory
from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface
from app.repositories.fstab_repository import FstabRepository
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
    def setup_mock_fstab_repository(
        fstab_content: str = "",
        proc_content: str = None,
        config_values=None
    ):
        """
        Sets up the common mocked FSTAB repository and configuration manager.
        :param fstab_content: The content of the fstab file
        :param proc_content: The content of the proc file
        :param config_values: The configuration values to use
        """

        # If no config values are provided, use the default values
        if config_values is None:
            config_values = TestHelper.default_config_values

        # If Proc is none, use the fstab content
        if proc_content is None:
            proc_content = fstab_content

        # Create a mock file system repository
        mock_fs_repository = MagicMock(spec=FileSystemRepositoryInterface)

        # Create a side effect for the read_file method
        def read_file_side_effect(file_path):
            if file_path == config_values["FSTAB_LOCATION"]:
                return fstab_content
            elif file_path == config_values["PROC_MOUNTS_LOCATION"]:
                return proc_content
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
        expected_lines = sorted([TestHelper.format_line(line) for line in expected_lines if line.strip()])
        actual_lines = sorted([TestHelper.format_line(line) for line in actual_lines if line.strip()])

        # Assert two lists are equal (ignoring order)
        return expected_lines == actual_lines

    @staticmethod
    def fstab_line(actual_path: str, mount_path: str, mount_type: MountType):
        """
        Create a formatted fstab line
        """
        cifs_file_location = TestHelper.default_config_values["CIFS_FILE_LOCATION"]
        cifs_domain = TestHelper.default_config_values["CIFS_DOMAIN"]
        ssh_file_location = TestHelper.default_config_values["LINUX_SSH_LOCATION"]
        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        if mount_type == MountType.WINDOWS:
            return f"{actual_path} {mount_path} cifs credentials={cifs_file_location},domain={cifs_domain},uid=1001,gid=5001,auto 0 0"
        elif mount_type == MountType.LINUX:
            return f"{ssh_user}@{actual_path} {mount_path} fuse.sshfs IdentityFile={ssh_file_location},uid=1001,gid=5001,auto 0 0"

    @staticmethod
    def windows_fstab_line(actual_path: str, mount_path: str):
        """
        Create a formatted fstab line for a windows mount
        """
        return TestHelper.fstab_line(actual_path, mount_path, MountType.WINDOWS)

    @staticmethod
    def linux_fstab_line(actual_path: str, mount_path: str):
        """
        Create a formatted fstab line for a linux mount
        """
        return TestHelper.fstab_line(actual_path, mount_path, MountType.LINUX)

    @staticmethod
    def get_last_write_content(mock_fs_repository):
        """
        Get the content of the last write file call
        """
        return mock_fs_repository.write_file.call_args[0][1]


class TestStoreMountInformation(unittest.TestCase):

    def test_store_mount_information_windows_success(self):
        """
        This test will simulate storing mounting information for a windows mount
        in the fstab file
        """

        # Mock the FSTAB content
        fstab_content = f"""
        {TestHelper.windows_fstab_line("/mnt/windows", "/system/mounts/windows")}
        {TestHelper.linux_fstab_line("/mnt/linux", "/system/mounts/linux")}
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
        {TestHelper.windows_fstab_line("/mnt/windows", "/system/mounts/windows")}
        {TestHelper.linux_fstab_line("/mnt/linux", "/system/mounts/linux")}
        {TestHelper.windows_fstab_line("/mnt/windows/folder", "/shares/windows")}
        """

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

    def test_store_mount_information_linux_success(self):
        """
        This test will simulate storing mounting information for a linux mount
        in the fstab file
        """

        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        # Mock the FSTAB content
        fstab_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windows", "/shares/windows1")}
            {TestHelper.linux_fstab_line("/mnt/linux", "/shares/linux1")}
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
            {TestHelper.windows_fstab_line("/mnt/windows", "/shares/windows1")}
            {TestHelper.linux_fstab_line("/mnt/linux", "/shares/linux1")}
            {TestHelper.linux_fstab_line("/linuxserver/mount", "/shares/linux2")}
            """

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
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

        # Mock the FSTAB content (include duplicates)
        fstab_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windows", "/shares/windows1")}
            {TestHelper.linux_fstab_line("/mnt/linux", "/shares/linux1")}
            {TestHelper.windows_fstab_line("/mnt/windows", "/shares/windows1")}
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create our mount
        mount = FakeMountFactory.windows_mount(
            mount_path="/shares/windows2",
            actual_path=f"/mnt/windows2"
        )

        # Run the store the mount information method
        fstab_repository.store_mount_information(mount)

        # Assert the content was written correctly
        expected_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windows", "/shares/windows1")}
            {TestHelper.linux_fstab_line("/mnt/linux", "/shares/linux1")}
            {TestHelper.windows_fstab_line("/mnt/windows2", "/shares/windows2")}
            """

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )


class TestRemoveMountInformation(unittest.TestCase):

    def test_remove_mount_information_windows_success(self):
        """
        This test will simulate removing mounting information for a windows mount
        """

        # Mock the FSTAB content
        fstab_content = f"""
        {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
        {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
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
        {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
        """

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

    def test_remove_mount_information_linux_success(self):
        """
        This test will simulate removing mounting information for a linux mount
        """

        ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        # Mock the FSTAB content
        fstab_content = f"""
        {TestHelper.linux_fstab_line("/mnt/linuxserver1", "/shares/linux1")}
        {TestHelper.linux_fstab_line("/mnt/linuxserver2", "/shares/linux2")}
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
        {TestHelper.linux_fstab_line("/mnt/linuxserver2", "/shares/linux2")}
        """

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )

    def test_remove_mount_information_mount_not_present_in_fstab(self):
        """
        Simulate removing a mount that is not present in the fstab file
        """

        # Don't need to provide any config values as the fstab should be empty
        fstab_repository = TestHelper.setup_mock_fstab_repository()

        # Create a mount that does not exist in the fstab file
        mount = FakeMountFactory.windows_mount(
            mount_path="/shares/windows",
            actual_path="/mnt/windows"
        )

        # Run the store the mount information method
        fstab_repository.remove_mount_information(mount.mount_path)

        # Assert the content was written correctly
        expected_content = ""

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )


class TestRemoveMounts(unittest.TestCase):

    def test_remove_multiple_mounts(self):
        """
        This test will simulate removing multiple mounts from the fstab file
        """

        linux_ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        # Mock the FSTAB content
        fstab_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            {TestHelper.linux_fstab_line("/mnt/linuxserver1", "/shares/linux1")}
            {TestHelper.linux_fstab_line("/mnt/linuxserver2", "/shares/linux2")}
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create a list of mounts to remove from the fstab file
        mounts = [
            FakeMountFactory.windows_mount(
                mount_path="/shares/windows1",
                actual_path="/mnt/windowserver1"
            ),
            FakeMountFactory.linux_mount(
                mount_path="/shares/linux2",
                actual_path=f"{linux_ssh_user}@/mnt/linuxserver2"
            )
        ]

        # Call the remove mounts method
        fstab_repository.remove_mounts(mounts)

        expected = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            {TestHelper.linux_fstab_line("/mnt/linuxserver1", "/shares/linux1")}
            """

        # Fetch the last content that was written to the write file method
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)

        self.assertTrue(
            TestHelper.compare_file_contents(expected, actual)
        )

    def test_remove_multiple_mounts_with_empty_fstab(self):
        """
        This test will simulate removing multiple mounts from the fstab file
        where some of the mounts do not exist in the fstab file
        """

        # Don't need to provide any config values as the fstab should be empty
        fstab_repository = TestHelper.setup_mock_fstab_repository()

        # Create a list of mounts to remove from the fstab file
        mounts = [
            FakeMountFactory.windows_mount(
                mount_path="/shares/windows1",
                actual_path="/mnt/windowserver1"
            ),
            FakeMountFactory.linux_mount(
                mount_path="/shares/linux2",
                actual_path="/mnt/linuxserver2"
            )
        ]

        # Call the remove mounts method
        fstab_repository.remove_mounts(mounts)

        expected = ""

        # Fetch the last content that was written to the write file method
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)

        self.assertTrue(
            TestHelper.compare_file_contents(expected, actual)
        )

    def test_remove_multiple_mounts_only_some_missing_mounts(self):
        """
        This test will simulate removing multiple mounts from the fstab file
        where some of the mounts do not exist in the fstab file
        """

        linux_ssh_user = TestHelper.default_config_values["LINUX_SSH_USER"]

        # Mock the FSTAB content
        fstab_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            {TestHelper.linux_fstab_line("/mnt/linuxserver1", "/shares/linux1")}
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content
        )

        # Create a list of mounts to remove from the fstab file
        mounts = [
            FakeMountFactory.windows_mount(
                mount_path="/shares/windows1",
                actual_path="/mnt/windowserver1"
            ),
            FakeMountFactory.linux_mount(
                mount_path="/shares/linux2",
                actual_path=f"{linux_ssh_user}@/mnt/linuxserver2"
            )
        ]

        # Call the remove mounts method
        fstab_repository.remove_mounts(mounts)

        expected = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            {TestHelper.linux_fstab_line("/mnt/linuxserver1", "/shares/linux1")}
            """

        # Fetch the last content that was written to the write file method
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)

        self.assertTrue(
            TestHelper.compare_file_contents(expected, actual)
        )


class TestIsMounted(unittest.TestCase):

    def test_is_mounted_true(self):
        """
        This test will simulate checking if a mount is mounted
        and it is mounted
        """

        # Mock the proc file content
        proc_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            proc_content=proc_content
        )

        # Check if the mount is mounted
        is_mounted = fstab_repository.is_mounted("/shares/windows1")

        self.assertTrue(is_mounted)

    def test_is_mounted_false(self):
        """
        This test will simulate checking if a mount is mounted and it is not mounted
        """

        # Mock the proc file content
        proc_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            proc_content=proc_content
        )

        # Check if the mount is mounted
        is_mounted = fstab_repository.is_mounted("/shares/windows3")

        self.assertFalse(is_mounted)


class TestCleanup(unittest.TestCase):

    def test_cleanup(self):
        """
        This test will simulate cleaning up the mount information
        """

        # Mock the FSTAB content with some duplicates and some mounts that are not in proc
        fstab_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            {TestHelper.linux_fstab_line("/mnt/linuxserver1", "/shares/linux1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            """

        # Mock the proc content to only have the first two mounts
        proc_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
            """

        fstab_repository = TestHelper.setup_mock_fstab_repository(
            fstab_content=fstab_content,
            proc_content=proc_content
        )

        # Call the cleanup method
        fstab_repository.cleanup()

        # Assert the content was written correctly
        expected_content = f"""
            {TestHelper.windows_fstab_line("/mnt/windowserver1", "/shares/windows1")}
            {TestHelper.windows_fstab_line("/mnt/windowserver2", "/shares/windows2")}
        """

        # Assert the content was written correctly
        actual = TestHelper.get_last_write_content(fstab_repository.fs_repository)
        self.assertTrue(
            TestHelper.compare_file_contents(expected_content, actual)
        )


if __name__ == '__main__':
    unittest.main()
