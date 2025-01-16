import json
import unittest
from unittest.mock import MagicMock, patch, mock_open

from app.enums.enums import MountType
from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.models.mount import Mount
from app.repositories.file_sytem_repository import FileSystemRepositoryInterface
from app.repositories.mount_config_repository import MountConfigRepository
from app.repositories.mount_repository import MountRepository
from app.util.config import ConfigManager


def setup_mount_config_repo(system_mounts: list[Mount] = None,
                            remove_failures: list[Mount] = None,
                            is_mounted: bool = True):

    """
    Helper method to set up a mock repository
    :param system_mounts - Optionally specify fake system mount info this mock should return
    :param remove_failures - Optionally specify a list of mounts that the repo failed to remove from the system
    :param is_mounted - Optionally specify if a mount is mounted
    """
    mock_config_repository = MagicMock(spec=MountConfigRepository)
    mock_config_repository.get_all_system_mounts.return_value = system_mounts or []
    mock_config_repository.remove_mounts.return_value = remove_failures or []
    mock_config_repository.is_mounted.return_value = is_mounted
    return mock_config_repository


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
    def setup_mock_config_repo(
        system_mounts: list[Mount] = None,
        remove_failures: list[Mount] = None,
        is_mounted: bool = True
    ):
        """
        Sets up the common mocked FSTAB repository and configuration manager.
        :param system_mounts: Optionally specify fake system mount info this mock should return
        :param remove_failures: Optionally specify a list of mounts that the repo failed to remove from the system
        :param is_mounted: Optionally specify if a mount is mounted
        """

        # Create the mock config repository
        mock_config_repository = setup_mount_config_repo(
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

        # Create a MountRepository
        return MountRepository(
            mock_config_manager,
            mock_config_repository,
            mock_fs_repository
        )


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
    def setUp(self):
        """
        Common setup for all tests.
        """
        self.mock_config_repository = setup_mount_config_repo()
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.config_values = {
            "LINUX_SSH_USER": "dave",
            "DESIRED_MOUNTS_FILE_PATH": "mounts.json",
        }
        self.mock_config_manager.get_config.side_effect = lambda key: self.config_values[key]
        self.mount_repo = MountRepository(self.mock_config_manager, self.mock_config_repository)

    @patch("builtins.open", new_callable=mock_open, read_data="[]")
    def test_get_desired_mounts_empty(self, _mock_json_open):
        """
        Simulate an empty desired mounts file.
        """
        current_mounts = self.mount_repo.get_desired_mounts()
        self.assertListEqual([], current_mounts)

    @patch("builtins.open", new_callable=mock_open)
    def test_get_desired_mounts_with_content(self, mock_json_open):
        """
        Simulate a desired mounts file with a few mounts.
        """

        # Mock the file to return some JSON
        mock_json_open.return_value.read.return_value = json.dumps(
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

        current_mounts = self.mount_repo.get_desired_mounts()
        self.assertListEqual(expected, current_mounts)

    @patch("builtins.open", new_callable=mock_open)
    def test_get_desired_mounts_linux(self, mock_json_open):
        """
        Check that when we get desired mounts, the Linux mounts
        will get populated with the SSH user.
        """
        mock_json_open.return_value.read.return_value = json.dumps(
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

        current_mounts = self.mount_repo.get_desired_mounts()
        self.assertListEqual(expected, current_mounts)


class TestGetOrphanMounts(unittest.TestCase):

    def test_get_orphan_mounts(self):
        """
        Simulate a case where we have some mounts in the system config
        that are not mounted on the system.
        """

        # Simulate a mix of our mounts with some system mounts
        mock_config_repository = setup_mount_config_repo(
            system_mounts=[
                Mount(mount_path="/shares/our/share/1", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/our/share2/2", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/orphan/path", actual_path="//Secret/share"),
            ]
        )

        # Create a side effect for the ismount method
        def ismount_side_effect(path):
            return path != "/shares/orphan/path"

        # Mock IsMount to return True for all mounts except the one we want to fail
        mock_config_repository.is_mounted.side_effect = ismount_side_effect

        # Create a mock config manager
        mock_config_manager = MagicMock(spec=ConfigManager)

        # Create the MountRepo
        mount_repo = MountRepository(
            mock_config_manager,
            mock_config_repository
        )

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
        self.mock_config_repository = setup_mount_config_repo(is_mounted=False)
        self.mock_config_manager = MagicMock(spec=ConfigManager)

        self.mount_repo = MountRepository(
            self.mock_config_manager,
            self.mock_config_repository
        )

        self.test_mount = Mount(
            mount_path="/shares/example",
            actual_path="//someServer/someShare",
            mount_type=MountType.WINDOWS,
        )

    def _mock_subprocess_and_path(self, mock_subprocess_run, mock_os_path, returncode=0, path_exists=True):
        """
        Helper to mock subprocess.run and os.path.exists.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=returncode)
        mock_os_path.exists.return_value = path_exists

    @patch("os.makedirs")
    @patch("os.path")
    @patch("subprocess.run")
    def test_mount_success(self, mock_subprocess_run, mock_os_path, _mock_os_makedirs):
        """
        Simulates a successful mount operation.
        """
        self._mock_subprocess_and_path(mock_subprocess_run, mock_os_path, returncode=0, path_exists=True)

        self.mount_repo.mount(self.test_mount)

        self.mock_config_repository.store_mount_information.assert_called_once()
        mock_subprocess_run.assert_called_once_with(
            ["sudo", "mount", "/shares/example"], capture_output=True
        )

    @patch("os.makedirs")
    @patch("os.path")
    @patch("subprocess.run")
    def test_mount_raises_exception(self, mock_subprocess_run, mock_os_path, _mock_os_makedirs):
        """
        Simulates a mount operation that fails.
        """

        # Make sure the return code is 2 (error)
        self._mock_subprocess_and_path(mock_subprocess_run, mock_os_path, returncode=2, path_exists=True)

        with self.assertRaises(MountException):
            self.mount_repo.mount(self.test_mount)


class TestUnmount(unittest.TestCase):

    def setUp(self):
        """
        Common setup for all tests.
        """
        self.mock_config_repository = setup_mount_config_repo()
        self.mock_config_manager = MagicMock(spec=ConfigManager)

        self.mount_repo = MountRepository(
            self.mock_config_manager,
            self.mock_config_repository
        )

    def _mock_subprocess_and_exists(self, mock_subprocess_run, mock_os_path_exists, returncode=0, path_exists=True):
        """
        Helper to mock subprocess.run and os.path.exists.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=returncode)
        mock_os_path_exists.return_value = path_exists

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("subprocess.run")
    def test_unmount_success(self, mock_subprocess_run, mock_shutil_rmtree, mock_os_path_exists):
        """
        Simulates a simple unmount operation.
        """
        self._mock_subprocess_and_exists(mock_subprocess_run, mock_os_path_exists, returncode=0, path_exists=False)

        self.mount_repo.unmount("/shares/example")

        self.mock_config_repository.remove_mount_information.assert_called_once()
        mock_shutil_rmtree.assert_called_once_with("/shares/example")

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("subprocess.run")
    def test_unmount_raises_exception(self, mock_subprocess_run, _mock_shutil_rmtree, mock_os_path_exists):
        """
        Simulates an unmount operation that fails.
        """

        # Make sure the return code is 2 (error)
        self._mock_subprocess_and_exists(mock_subprocess_run, mock_os_path_exists, returncode=2, path_exists=False)

        with self.assertRaises(UnmountException):
            self.mount_repo.unmount("/shares/example")

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("subprocess.run")
    def test_unmount_raises_exception_with_remove_mount_point(self, mock_subprocess_run, mock_shutil_rmtree, mock_os_path_exists):
        """
        Simulates an unmount operation that fails on removing the mount point.
        """
        self._mock_subprocess_and_exists(mock_subprocess_run, mock_os_path_exists, returncode=0, path_exists=False)

        mock_shutil_rmtree.side_effect = PermissionError("Cannot remove directory for some reason")

        with self.assertRaises(UnmountException):
            self.mount_repo.unmount("/shares/example")

    @patch("os.listdir")
    @patch("os.path.exists")
    @patch("shutil.rmtree")
    @patch("subprocess.run")
    def test_unmount_with_contents_in_mount_point(self, mock_subprocess_run, _mock_shutil_rmtree, mock_os_path_exists, mock_listdir):
        """
        Simulates an unmount operation that fails because the mount point has contents.
        """

        # By making path_exists True, we simulate that the mount point exists
        self._mock_subprocess_and_exists(mock_subprocess_run, mock_os_path_exists, returncode=0, path_exists=True)

        # We then mock the mount point containing files
        mock_listdir.return_value = ["file1.txt", "file2.txt"]

        with self.assertRaises(UnmountException):
            self.mount_repo.unmount("/shares/example")


class TestUnmountAll(unittest.TestCase):

    def setUp(self):
        """
        Common setup for all unmount tests.
        """
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        self.mock_config_repository = MagicMock(spec=MountConfigRepository)
        self.mount_repo = MountRepository(self.mock_config_manager, self.mock_config_repository)

    @patch.object(MountRepository, '_perform_unmount')
    @patch.object(MountRepository, '_remove_mount_point')
    def test_unmount_all_success(self, mock_remove_mount_point, mock_perform_unmount):
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

        # Simulate no failure during unmounting
        mock_perform_unmount.return_value = None
        mock_remove_mount_point.return_value = None

        # Call unmount_all
        failed_mounts = self.mount_repo.unmount_all()

        # Assert that no mounts failed to unmount
        self.assertListEqual(failed_mounts, [])

    @patch.object(MountRepository, '_perform_unmount')
    @patch.object(MountRepository, '_remove_mount_point')
    def test_unmount_all_failure(self, mock_remove_mount_point, mock_perform_unmount):
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

        # Simulate a failure on the second unmount operation
        mock_perform_unmount.side_effect = [None, UnmountException("Unmount failed for some reason")]
        mock_remove_mount_point.return_value = None

        # Call unmount_all
        failed_mounts = self.mount_repo.unmount_all()

        # Assert the second mount failed to unmount
        self.assertListEqual(failed_mounts, [mounts_to_unmount[1]])

    @patch.object(MountRepository, '_perform_unmount')
    @patch.object(MountRepository, '_remove_mount_point')
    def test_unmount_all_no_mounts(self, mock_remove_mount_point, mock_perform_unmount):
        """
        Test the unmount_all method when there are no mounts to unmount.
        """

        # Mock the behavior of get_current_mounts to return an empty list
        self.mount_repo.get_current_mounts = MagicMock(return_value=[])

        # Call unmount_all
        failed_mounts = self.mount_repo.unmount_all()

        # Assert that the returned list is empty
        self.assertListEqual(failed_mounts, [])


if __name__ == '__main__':
    unittest.main()
