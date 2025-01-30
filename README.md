# Mounty Python

App to manage mounts on a VM

## Pre-requisites

This app requires a `.env` file in the root directory with the following variables:

| Key                      | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| DESIRED_MOUNTS_FILE_PATH | The path to `mounts.json` or another file that specifies the desired mounts |
| CIFS_FILE_LOCATION       | The path to the file that contains the credentials for the CIFS mounts      |
| LINUX_SSH_USER           | The user to use for SSH connections to the Linux shares                     |
| LINUX_SSH_LOCATION       | The path to the SSH key for the Linux shares                                |


## Running the script

There are three main commands that can be run:

- `python3 run.py --dry-run` - Simulates the mounting script without actually mounting anything
- `python3 run.py --unmount-all` - Remove all the manually mounted shares (including the mount points)
- `python3 run.py --cleanup` - Will cleanup the FSTAB file (remove duplicates and any stale mounts)
- `python3 run.py` - Mount the shares specified in the `mounts.json` file

### Running from bash

The scripts can also be run from a bash script, which will also setup a VIRTUAL environment and install the required dependencies:

- `sh run.sh --dry-run`
- `sh run.sh --unmount-all`
- `sh run.sh --cleanup`
- `sh run.sh`

## Different mounting methods

### FSTAB Mounts

The first method of mounting is by adding the mounts to the `/etc/fstab` file. This will mount the shares on boot and will be available to all users.

The advantage of this method is that the shares will be mounted automatically on boot, but the disadvantage is that it consumes more resources and can potentially cause errors when booting if the shares are not available.

### AutoMount

The second method of mounting is by using the `autofs` service. This will mount the shares when they are accessed and will unmount them after a period of inactivity.

The advantage of this method is that it consumes fewer resources and will not cause errors if the shares are not available. The disadvantage is that the shares will not be available on boot and will only be mounted when accessed, this can cause a delay when accessing the shares for the first time or if the shares have not been accessed for a while.