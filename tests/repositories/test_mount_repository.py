import json
import unittest
from unittest.mock import MagicMock, patch, mock_open

from app.enums.enums import MountType
from app.exceptions.cleanup_exception import CleanupException
from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.models.mount import Mount
from app.interfaces.file_sytem_repository_interface import FileSystemRepositoryInterface
from app.interfaces.mount_config_repository_interface import MountConfigRepository
from app.repositories.mount_repository import MountRepository
from app.util.config import ConfigManager


class TestHelper:

    default_config_values = {
        "FSTAB_LOCATION": "/etc/fstab",
        "PROC_MOUNTS_LOCATION": "/proc/mounts",
        "CIFS_FILE_LOCATION": "/etc/.cifs",
        "LINUX_SSH_LOCATION": "/root/.ssh/id_rsa_linux",
        "LINUX_SSH_USER": "dave",
        "CIFS_DOMAIN": "ONS",
        "DESIRED_MOUNTS_FILE_PATH": "mounts.json",
    }

    @staticmethod
    def setup_mock_config_repo(
        system_mounts: list[Mount] = None,
        mounts_content: str = "{}",
        remove_failures: list[Mount] = None,
        is_mounted: bool = True,
        config_values: dict = None,
    ):
        """
        Sets up the common mocked FSTAB repository and configuration manager.
        :param system_mounts: Optionally specify fake system mount info this mock should return
        :param mounts_content: Optionally specify the content of the desired mounts file
        :param remove_failures: Optionally specify a list of mounts that the repo failed to remove from the system
        :param is_mounted: Optionally specify if a mount is mounted
        :param config_values: Optionally specify a dictionary of config values to use
        """

        # Use default config values if none are provided
        config_values = config_values or TestHelper.default_config_values

        # Create the mock config repository
        mock_config_repository = TestHelper.setup_mount_config_repo(
            system_mounts=system_mounts or [],
            remove_failures=remove_failures or [],
            is_mounted=is_mounted
        )

        # Create the mock config manager
        mock_config_manager = MagicMock(spec=ConfigManager)

        # Set the default config values
        mock_config_manager.get_config.side_effect = lambda key: TestHelper.default_config_values[key]

        # Create a mock file system repository
        mock_fs_repository = MagicMock(spec=FileSystemRepositoryInterface)

        def read_file_side_effect(file_path):
            if file_path == config_values["DESIRED_MOUNTS_FILE_PATH"]:
                return mounts_content
            return ""

        # Set the side effect for the read_file method
        mock_fs_repository.read_file.side_effect = read_file_side_effect

        # Create a MountRepository
        return MountRepository(
            mock_config_manager,
            mock_config_repository,
            mock_fs_repository
        )

    @staticmethod
    def setup_mount_config_repo(system_mounts: list[Mount] = None,
                                remove_failures: list[Mount] = None,
                                is_mounted: bool = True):
        """
        Helper method to set up a mock config repository
        :param system_mounts - Optionally specify fake system mount info this mock should return
        :param remove_failures - Optionally specify a list of mounts that the repo failed to remove from the system
        :param is_mounted - Optionally specify if a mount is mounted
        """
        mock_config_repository = MagicMock(spec=MountConfigRepository)
        mock_config_repository.get_all_system_mounts.return_value = system_mounts or []
        mock_config_repository.remove_mounts.return_value = remove_failures or []
        mock_config_repository.is_mounted.return_value = is_mounted
        return mock_config_repository


class TestGetCurrentMounts(unittest.TestCase):

    def run_test(self, system_mounts, expected_mounts):
        """
        Helper method to test `get_current_mounts` with various inputs.
        """

        # Create a mount repository
        mount_repo = TestHelper.setup_mock_config_repo(
            system_mounts=system_mounts
        )

        # Run the get_current_mounts
        current_mounts = mount_repo.get_current_mounts()

        # Assert the list matches expected mounts
        self.assertListEqual(expected_mounts, current_mounts)

    def test_get_current_mounts_only(self):
        """
        Test when the system only has our mounts (no system mounts).
        """
        system_mounts = [
            Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
        ]

        self.run_test(system_mounts=system_mounts, expected_mounts=system_mounts)

    def test_get_current_mounts_with_some_system_mounts(self):
        """
        Test when the system has a mix of our mounts and unrelated system mounts.
        """
        system_mounts = [
            Mount(mount_path="/user/important/thing", actual_path="//Secret/share/elsewhere"),
            Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/root/system/thing", actual_path="//Secret/share"),
        ]

        expected_mounts = [
            Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
        ]

        self.run_test(system_mounts=system_mounts, expected_mounts=expected_mounts)


class TestGetDesiredMounts(unittest.TestCase):

    def test_get_desired_mounts_empty(self):
        """
        Simulate an empty desired mounts file.
        """
        mount_repo = TestHelper.setup_mock_config_repo()
        current_mounts = mount_repo.get_desired_mounts()
        self.assertListEqual([], current_mounts)

    def test_get_desired_mounts_with_content(self):
        """
        Simulate a desired mounts file with a few mounts.
        """

        # Mock the file to return some JSON
        json_content = json.dumps(
            [
                {
                    "mount_path": "/shares/outputs/example_data",
                    "actual_path": "//ny334xx/EXAMPLE_LOCATION/PROD/ETC",
                    "mount_type": "cifs",
                },
                {
                    "mount_path": "/shares/inputs/another_example",
                    "actual_path": "example:/abc/live/location/example",
                    "mount_type": "fuse.sshfs",
                },
            ]
        )

        mount_repo = TestHelper.setup_mock_config_repo(
            mounts_content=json_content
        )

        expected = [
            Mount(
                mount_path="/shares/outputs/example_data",
                actual_path="//ny334xx/EXAMPLE_LOCATION/PROD/ETC",
                mount_type=MountType.WINDOWS,
            ),
            Mount(
                mount_path="/shares/inputs/another_example",
                actual_path="dave@example:/abc/live/location/example",
                mount_type=MountType.LINUX,
            ),
        ]

        current_mounts = mount_repo.get_desired_mounts()
        self.assertListEqual(expected, current_mounts)

    def test_get_desired_mounts_linux(self):
        """
        Check that when we get desired mounts, the Linux mounts
        will get populated with the SSH user.
        """
        json_content = json.dumps(
            [
                {
                    "mount_path": "/shares/linux/inputs",
                    "actual_path": "/linuxsever/inputs/folder",
                    "mount_type": "fuse.sshfs",
                },
                {
                    "mount_path": "/shares/linux/output",
                    "actual_path": "/linuxsever/outputs/folder",
                    "mount_type": "fuse.sshfs",
                },
            ]
        )

        mount_repo = TestHelper.setup_mock_config_repo(
            mounts_content=json_content
        )

        expected = [
            Mount(
                mount_path="/shares/linux/inputs",
                actual_path="dave@/linuxsever/inputs/folder",
                mount_type=MountType.LINUX,
            ),
            Mount(
                mount_path="/shares/linux/output",
                actual_path="dave@/linuxsever/outputs/folder",
                mount_type=MountType.LINUX,
            ),
        ]

        current_mounts = mount_repo.get_desired_mounts()
        self.assertListEqual(expected, current_mounts)


class TestGetOrphanMounts(unittest.TestCase):

    def test_get_orphan_mounts(self):
        """
        Simulate a case where we have some mounts in the system config
        that are not mounted on the system.
        """

        system_mounts = [
            Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/orphan/path", actual_path="//Secret/share"),
        ]

        # Create a mount repository
        mount_repo = TestHelper.setup_mock_config_repo(
            system_mounts=system_mounts,
        )

        # Create a side effect for the ismount method
        def ismount_side_effect(path):
            return path != "/shares/orphan/path"

        # Mock IsMount to return True for all mounts except the one we want to fail
        mount_repo.mount_config_repository.is_mounted.side_effect = ismount_side_effect

        # Run the get orphans method
        orphan_mounts = mount_repo.get_orphan_mounts()

        # Assert the list matches our shares
        self.assertListEqual(
            [
                Mount(mount_path="/shares/orphan/path", actual_path="//Secret/share"),
            ],
            orphan_mounts
        )


class TestMount(unittest.TestCase):
    def setUp(self):
        """
        Common setup for all tests.
        """

        self.mount_repo = TestHelper.setup_mock_config_repo(
            is_mounted=False
        )

        self.test_mount = Mount(
            mount_path="/shares/example",
            actual_path="//someServer/someShare",
            mount_type=MountType.WINDOWS,
        )

    @patch("subprocess.run")
    def test_mount_success(self, mock_subprocess_run):
        """
        Simulates a successful mount operation.
        """

        # Ensure the mount operation returns 0
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        self.mount_repo.mount(self.test_mount)

        # Assert the mount information was saved
        self.mount_repo.mount_config_repository.store_mount_information.assert_called_once_with(self.test_mount)
        mock_subprocess_run.assert_called_once_with(
            ["sudo", "mount", "/shares/example"], capture_output=True
        )

    @patch("subprocess.run")
    def test_mount_raises_exception(self, mock_subprocess_run):
        """
        Simulates a mount operation that fails.
        """

        # Mock subprocess.run to return a non-zero return code
        mock_subprocess_run.return_value = MagicMock(returncode=2)

        with self.assertRaises(MountException):
            self.mount_repo.mount(self.test_mount)

    @patch("subprocess.run")
    def test_mount_with_contents_in_folder(self, mock_subprocess_run):
        """
        Simulates a mount operation that fails because the mount point has contents.
        """

        # Ensure the mount operation returns 0
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        # Mock the directory_empty method to return False
        self.mount_repo.fs_repository.directory_empty.return_value = False

        with self.assertRaises(MountException):
            self.mount_repo.mount(self.test_mount)


class TestUnmount(unittest.TestCase):

    def setUp(self):
        """
        Common setup for all tests.
        """
        self.mount_repo = TestHelper.setup_mock_config_repo(
            is_mounted=True
        )

    @patch("subprocess.run")
    def test_unmount_success(self, mock_subprocess_run):
        """
        Simulates a simple unmount operation.
        """

        # Ensure a successful unmount operation
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        self.mount_repo.unmount("/shares/example")

        # Assert mount information was removed
        self.mount_repo.mount_config_repository.remove_mount_information.assert_called_once_with("/shares/example")

        # Assert the mount point was removed
        self.mount_repo.fs_repository.remove_directory.assert_called_once_with("/shares/example")

    @patch("subprocess.run")
    def test_unmount_raises_exception(self, mock_subprocess_run):
        """
        Simulates an unmount operation that fails.
        """

        # Mock the subprocess.run to return a non-zero return code
        mock_subprocess_run.return_value = MagicMock(returncode=2)

        with self.assertRaises(UnmountException):
            self.mount_repo.unmount("/shares/example")

    @patch("subprocess.run")
    def test_unmount_raises_exception_with_remove_mount_point(self, mock_subprocess_run):
        """
        Simulates an unmount operation that fails on removing the mount point.
        """

        # Ensure the subprocess.run returns 0
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        # But ensure the remove_directory method raises an exception
        self.mount_repo.fs_repository.remove_directory.side_effect = UnmountException("Failed to remove mount point")

        with self.assertRaises(UnmountException):
            self.mount_repo.unmount("/shares/example")


class TestUnmountAll(unittest.TestCase):

    def setUp(self):
        """
        Common setup for all unmount tests.
        """
        self.mount_repo = TestHelper.setup_mock_config_repo(
            is_mounted=True
        )

    def test_unmount_all_success(self):
        """
        Test the unmount_all method when all unmount operations are successful.
        """

        # Define the mounts to be unmounted
        mounts_to_unmount = [
            Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/our/share/2", actual_path="//SomeServer/Somewhere")
        ]

        # Mock the behavior of get_current_mounts
        self.mount_repo.get_current_mounts = MagicMock(return_value=mounts_to_unmount)

        # Make the unmount operations successful
        self.mount_repo._perform_unmount = MagicMock(return_value=True)
        self.mount_repo._remove_mount_point = MagicMock(return_value=True)

        # Call unmount_all
        failed_mounts = self.mount_repo.unmount_all()

        # Assert that no mounts failed to unmount
        self.assertListEqual(failed_mounts, [])

    def test_unmount_all_failure(self):
        """
        Test the unmount_all method when some unmount operations fail.
        """

        # Define the mounts to be unmounted
        mounts_to_unmount = [
            Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
            Mount(mount_path="/shares/our/share/2", actual_path="//SomeServer/Somewhere")
        ]

        # Mock the behavior of get_current_mounts
        self.mount_repo.get_current_mounts = MagicMock(return_value=mounts_to_unmount)

        # Simulate a failure on the second mount
        self.mount_repo._perform_unmount = MagicMock(
            side_effect=[None, UnmountException("Unmount failed for some reason")]
        )
        self.mount_repo._remove_mount_point = MagicMock(return_value=True)

        # Call unmount_all
        failed_mounts = self.mount_repo.unmount_all()

        # Assert the second mount failed to unmount
        self.assertListEqual(failed_mounts, [mounts_to_unmount[1]])

    def test_unmount_all_no_mounts(self):
        """
        Test the unmount_all method when there are no mounts to unmount.
        """

        # Mock the behavior of get_current_mounts to return an empty list
        self.mount_repo.get_current_mounts = MagicMock(return_value=[])

        # Call unmount_all
        failed_mounts = self.mount_repo.unmount_all()

        # Assert that the returned list is empty
        self.assertListEqual(failed_mounts, [])


class TestCleanup(unittest.TestCase):

    def setUp(self):
        """
        Common setup for all cleanup tests.
        """
        self.mount_repo = TestHelper.setup_mock_config_repo(
            is_mounted=True
        )

    def test_cleanup_exception(self):
        """
        This test will simulate a failure during the cleanup process.
        """

        # Mock the behavior of the cleanup method
        self.mount_repo.mount_config_repository.cleanup.side_effect = Exception("Something went wrong")

        with self.assertRaises(CleanupException):
            self.mount_repo.cleanup()



if __name__ == '__main__':
    unittest.main()
