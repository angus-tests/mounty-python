from enum import Enum


class MountType(Enum):
    """
    Types for our file share mounts
    windows, linux etc
    """

    WINDOWS = "cifs"
    LINUX = "fuse.sshfs"
    HOST = "host"
    NONE = "none"

    @staticmethod
    def from_str(x: str):
        """
        Convert a string to a MountType enum.
        :return MountType
        """
        for mount_type in MountType:
            if x.upper() == mount_type.value.upper():
                return MountType[mount_type.name]

        return MountType.NONE
