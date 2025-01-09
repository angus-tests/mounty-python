# Mounty Python

App to manage mounts on a VM

## Pre-requisites

This app requires a `.env` file in the root directory with the following variables:

```
DESIRED_MOUNTS_PATH: The path to mounts.json or another file that specifies the desired mounts

CIFS_FILE_LOCATION: The path to the file that contains the credentials for the CIFS mounts

LINUX_SSH_USER: The user to use for SSH connections to the Linux shares

LINUX_SSH_LOCATION: The path to the SSH key for the Linux shares
```