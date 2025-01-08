import unittest
from unittest.mock import MagicMock, call

from app.models.mount import Mount
from app.repositories.mount_repository import MountRepositoryInterface
from app.services.mounting_service import MountingService


class TestMountingServiceRun(unittest.TestCase):

    def setUpMockRepository(self, desired_mounts=None, current_mounts=None):
        """
        Helper method to set up a mock repository with the specified desired and current mounts.
        """
        mock_repository = MagicMock(spec=MountRepositoryInterface)
        mock_repository.get_desired_mounts.return_value = desired_mounts or []
        mock_repository.get_current_mounts.return_value = current_mounts or []
        mock_repository.mount.return_value = None
        mock_repository.unmount.return_value = None
        return mock_repository

    def test_add_new_mounts(self):
        """
        This test simulates a mounts.json file with two mounts in it
        and no mounts currently on the system.
        """
        # Set up the mock repository
        mock_repository = self.setUpMockRepository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ],
            current_mounts=[]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        mounting_service.run()

        # Assertions
        self.assertEqual(2,  mock_repository.mount.call_count)
        self.assertEqual(0, mock_repository.unmount.call_count)

    def test_remove_old_mounts(self):
        """
        This test simulates a mounts.json file with a single mount in it
        and two mounts currently on the system (including the one in the mounts.json file).
        """
        # Set up the mock repository
        mock_repository = self.setUpMockRepository(
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
        mounting_service.run()

        # Assertions
        self.assertEqual(0, mock_repository.mount.call_count)
        self.assertEqual(1, mock_repository.unmount.call_count)

        mock_repository.unmount.assert_called_with(
            Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere")
        )

    def test_update_mounts(self):
        """
        This test simulates a mounts.json file with a single mount in it
        and two mounts currently on the system (including the one in the mounts.json file).
        The mount in the mounts.json file has a different actual path to the one currently on the system.
        """

        # Set up the mock repository
        mock_repository = self.setUpMockRepository(
            desired_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse"),
            ],
            current_mounts=[
                Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere"),
                Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere"),
            ]
        )

        # Create the mounting service
        mounting_service = MountingService(mock_repository)

        # Run the mounting service
        mounting_service.run()

        # Assertions
        self.assertEqual(1, mock_repository.mount.call_count)
        self.assertEqual(2, mock_repository.unmount.call_count)

        # Assert unmount was called with correct mounts
        mock_repository.mount.assert_has_calls([
            call(Mount(mount_path="/shares/test", actual_path="//SomeServer/Somewhere")),
            call(Mount(mount_path="/shares/test2", actual_path="//AnotherServer/Somewhere")),
        ])

        # Assert mount was called with correct mount
        mock_repository.mount.assert_called_with(
            Mount(mount_path="/shares/test", actual_path="//SomeServer/SomewhereElse")
        )


if __name__ == '__main__':
    unittest.main()
