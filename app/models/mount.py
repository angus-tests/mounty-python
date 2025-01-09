import re
from dataclasses import dataclass

from app.enums.enums import MountType


@dataclass(order=True)
class Mount:
    """
    A mount is made up of...
    mount_path: The directory on the current machine
    actual_path: The directory the mount maps to
    mount_type: The type of mount
    """
    mount_path: str
    actual_path: str
    mount_type: MountType = MountType.NONE

    def __eq__(self, other) -> bool:
        """
        Compare two mounts
        :param other: Another mount
        """
        # TODO abstract this away?
        # Remove the user from the SSH path
        normalised_actual = re.sub(r".+?@", "", self.actual_path)
        normalised_actual_other = re.sub(r".+?@", "", other.actual_path)

        return ((self.mount_path == other.mount_path)
                and (normalised_actual == normalised_actual_other and self.mount_type == other.mount_type))

