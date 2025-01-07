from app.repositories.mount_repository import MountRepositoryInterface


class MountingService:

    def __init__(self, mount_repository: MountRepositoryInterface):
        self.mount_repository = mount_repository

    def run(self):
        """
        Run the mounting service
        """

        # Find mounts to add

        # Find mounts to remove

        # Find mounts to update

        # Log any failed mounts

        # Return status
        pass
