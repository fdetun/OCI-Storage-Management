OCI Storage Management

A Python script to interact with Oracle Cloud Infrastructure (OCI) Object Storage. The script provides various methods for managing files and folders in the storage, such as listing files in a bucket, checking if a folder exists, compressing and uploading images, deleting files in bulk, and uploading files in bulk to a folder.

Installation

1. Install the required Python packages using `pip`:

pip install oci Pillow

2. Set up your OCI configuration file (usually located at `~/.oci/config`) with the necessary API keys and access credentials. For more information, refer to the official OCI documentation: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm

Usage

You can run the script with the following commands:

- To list all files in the bucket:

python oci_storage.py --list-files

- To check if a folder exists in the bucket:

python oci_storage.py --check-folder FOLDER_NAME

- To upload files from a local folder to a destination folder in the bucket:

python oci_storage.py --upload-folder /path/to/local/folder --destination-folder destination_folder

- To delete files in bulk from a folder in the bucket:

python oci_storage.py --delete-folder FOLDER_NAME

