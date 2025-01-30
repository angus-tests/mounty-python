
from abc import ABC


class RunStrategyInterface(ABC):
    """
    Interface for run strategies, which are responsible for
    executing the application logic, e.g main, unmount_all, etc.
    """

    def main(self):
        """
        - Mount all specified mounts
        - Unmount all orphan mounts
        - Update stale mounts
        """
        raise NotImplementedError
    
    def dry_run(self):
        """
        - Dry run the main method
        """
        raise NotImplementedError
    
    def unmount_all(self):
        """
        - Unmount all our mounts
        - Remove the mount points
        """
        raise NotImplementedError
    
    def info(self):
        """
        - Get information about the current mounts
        """
        raise NotImplementedError
    


