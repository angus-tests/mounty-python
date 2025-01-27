import unittest
from unittest.mock import MagicMock, call

from app.exceptions.mount_exception import MountException
from app.exceptions.unmount_exception import UnmountException
from app.facades.log_facade import LogFacade
from app.models.mount import Mount
from app.interfaces.mount_repository import MountRepositoryInterface
from app.services.mounting_service import MountingService


def setup_mock_repository(desired_mounts: list[Mount] = None,
                          current_mounts: list[Mount] = None,
                          unmount_failures: list[Mount] = None):
    """
    Helper method to set up a mock repository with the specified desired and current mounts.
    :param desired_mounts - Optionally specify what desired mounts this mock should return
    :param current_mounts - Optionally specify the current system mounts this mock should return
    :param unmount_failures - Optionally specify a list of mounts that failed to unmount
    """
    mock_repository = MagicMock(spec=MountRepositoryInterface)

    # We only need to specify mock methods that do NOT return None
    mock_repository.get_desired_mounts.return_value = desired_mounts or []
    mock_repository.get_current_mounts.return_value = current_mounts or []
    mock_repository.unmount_all.return_value = unmount_failures or []
    return mock_repository


class TestMountingServiceRun(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        LogFacade.disable_logging()

    def test_add_new_mounts(self):
        """
        This test simulates a mounts.json file with two mounts in it
        and no mounts currently on the system.
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ],
            current_mounts=[]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertTrue(result)
        self.assertEqual(2,  mock_repository.mount.call_count)
        self.assertEqual(0, mock_repository.unmount.call_count)

    def test_remove_old_mounts(self):
        """
        This test simulates a mounts.json file with a single mount in it
        and two mounts currently on the system (including the one in the mounts.json file).
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
            ],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertTrue(result)
        self.assertEqual(0, mock_repository.mount.call_count)
        self.assertEqual(1, mock_repository.unmount.call_count)

        mock_repository.unmount.assert_called_with(
            "/shares/test2"
        )

    def test_update_mounts(self):
        """
        This test simulates a mounts.json file with a single mount in it
        a single mount currently on the system (different actual path).
        """

        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse"),
            ],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertTrue(result)
        self.assertEqual(1, mock_repository.mount.call_count)
        self.assertEqual(1, mock_repository.unmount.call_count)

        # Assert unmount was called with correct mounts
        mock_repository.unmount.assert_called_with(
            "/shares/test"
        )

        # Assert mount was called with correct mount
        mock_repository.mount.assert_called_with(
            Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse")
        )

    def test_add_remove_and_update(self):
        """
        This test simulates a mounts.json file with two mounts in it
        and two mounts currently on the system (one of which is in the mounts.json file).

        The test should:
        - Add the new mount
        - Remove the old mount
        - Update the mount
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test3", actual_path="//AnotherServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertTrue(result)
        self.assertEqual(2, mock_repository.mount.call_count)
        self.assertEqual(2, mock_repository.unmount.call_count)

        # Assert unmount was called with correct mounts
        mock_repository.unmount.assert_has_calls([
            call("/shares/test"),
            call("/shares/test3")
        ], any_order=True)

        # Assert mount was called with correct mounts
        mock_repository.mount.assert_has_calls([
            call(Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse")),
            call(Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere")),
        ], any_order=True)

    def test_add_new_mounts_with_exception(self):
        """
        simulate an exception in the mount repository when adding a mount
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ],
            current_mounts=[]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Set up the mock repository to raise an exception when mounting
        mock_repository.mount.side_effect = MountException("Failed to mount for some reason")

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(2, mock_repository.mount.call_count)
        self.assertEqual(0, mock_repository.unmount.call_count)

    def test_remove_old_mounts_with_exception(self):
        """
        simulate an exception in the mount repository when removing a mount
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
            ],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Set up the mock repository to raise an exception when unmounting
        mock_repository.unmount.side_effect = UnmountException("Failed to unmount for some reason")

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(0, mock_repository.mount.call_count)
        self.assertEqual(1, mock_repository.unmount.call_count)

    def test_update_mounts_with_exception(self):
        """
        simulate an exception in the mount repository when updating a mount
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse"),
            ],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Set up the mock repository to raise an exception when unmounting
        mock_repository.unmount.side_effect = UnmountException("Failed to unmount for some reason")

        # Run the mounting service
        result = mounting_service.run()

        # Assertions
        self.assertFalse(result)
        self.assertEqual(0, mock_repository.mount.call_count)
        self.assertEqual(1, mock_repository.unmount.call_count)


class TestMountingServiceUnmountAll(unittest.TestCase):
    
    def test_unmount_all(self):
        """
        This test simulates a mounts.json file with two mounts in it
        and two mounts currently on the system.
        """
        # Set up the mock repository
        mock_repository = setup_mock_repository(
            desired_mounts=[],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        mounting_service.unmount_all()

        # Assertions
        self.assertEqual(1, mock_repository.unmount_all.call_count)


if __name__ == '__main__':
    unittest.main()
