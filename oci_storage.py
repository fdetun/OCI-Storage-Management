import os
import six
import oci
import io
import glob
from PIL import Image
from tempfile import SpooledTemporaryFile
import mimetypes
import argparse


class OciStorage(object):
    """
    OCI Storage Helper
    """

    def __init__(self, access_key_id=None, access_key_secret=None, end_point=None, bucket_name=None, expire_time=None):
        self.config = self._get_config("~/.oci/config", "DEFAULT")
        self.bucket = oci.object_storage.ObjectStorageClient(self.config)
        self.namespace = self.bucket.get_namespace().data
        self.bucket_name = ""

    def _get_config(self, path, default):
        config = oci.config.from_file(path, default)
        if config is not None:
            if isinstance(config, six.string_types):
                return config.strip()
            else:
                return config
        else:
            print("'%s not found in env variables or setting.py")

    def list_files_in_bucket(self, bucket_name=None):
        """method to list all files in a given bucket"""

        if bucket_name is None:
            bucket_name = self.bucket_name
        # List all objects in the bucket
        list_objects_response = self.bucket.list_objects(self.namespace, bucket_name)

        # Iterate over the list of objects and print their names
        for object_summary in list_objects_response.data.objects:
            print(object_summary.name)

    def check_folder_exist(self, directory_name, bucket_name=None):
        """method to check a folder exists in a given bucket"""
        if bucket_name is None:
            bucket_name = self.bucket_name
        folder_exists = False

        # List all objects in the bucket with the prefix of the directory name
        list_objects_response = self.bucket.list_objects(self.namespace, bucket_name, prefix=directory_name)

        # Check if the directory exists by iterating over the list of objects and checking for a matching prefix
        for object_summary in list_objects_response.data.objects:
            if object_summary.name.startswith(directory_name + '/'):
                folder_exists = True
                break
        return folder_exists

    def compress_image_file(self, content, quality=75, max_size=(800, 800)):
        """
        Modified version of the original save method that compresses images before uploading to S3.
        """
        # Check if the content is an image
        try:
            img = Image.open(content)
        except Exception as e:
            print(f"Error while opening image: {e}")
            img = None
        # If the content is an image, compress it
        if img is not None:
            # Resize the image to a maximum width of 800 pixels
            width, height = img.size
            if width > 800:
                new_height = int(height * 800 / width)
                img = img.resize((800, new_height))
            # Set the quality of the image to 80%

            img = img.convert('RGB')
            img_io = SpooledTemporaryFile(max_size=10485760)
            img.save(img_io, format='JPEG', optimize=True, quality=80)
            img_io.seek(0)
            content = img_io
            del img
            return content

    def bulk_delete(self, directory_name, bucket_name=None):
        """method to delete files in bulk from a given folder"""

        list_objects_response = self.bucket.list_objects(self.namespace, self.bucket_name, prefix=directory_name)
        for file_name in list_objects_response.data.objects:
            try:
                self.bucket.delete_object(self.namespace, self.bucket_name, file_name.name)
                print(f"File '{file_name.name}' deleted successfully from OCI Object Storage bucket '{self.bucket_name}'.")
            except FileNotFoundError:
                print("The file was not found")
            except Exception as e:
                print("An error occurred:", str(e))

    def bulk_upload_to_folder(self, source_folder, directory_name, bucket_name=None):
        if bucket_name is None:
            bucket_name = self.bucket_name
        folder_exists = self.check_folder_exist(directory_name)
        file_list = glob.glob(os.path.join(source_folder, "*"))
        for file_path in file_list:
            file_name = os.path.basename(file_path)
            content_type, _ = mimetypes.guess_type(file_path)
            # Check if the file is an image
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                with open(file_path, 'rb') as f:
                    img = self.compress_image_file(f)
                    self.bucket.put_object(namespace_name=self.namespace, bucket_name=bucket_name, object_name=os.path.join(directory_name, file_name), put_object_body=img, content_type=content_type)
                    print(f"File '{file_name}' uploaded successfully to OCI Object Storage bucket '{bucket_name}'.")
            else:
                try:
                    with open(file_path, 'rb') as f:
                        self.bucket.put_object(self.namespace, bucket_name, os.path.join(directory_name, file_name), f, content_type=content_type)
                    print(f"File '{file_name}' uploaded successfully to OCI Object Storage bucket '{bucket_name}'.")
                except FileNotFoundError:
                    print("The file was not found")
                except Exception as e:
                    print("An error occurred:", str(e))

def main(args):
    oci_storage = OciStorage()

    if args.list_files:
        oci_storage.list_files_in_bucket()

    if args.check_folder:
        oci_storage.check_folder_exist(args.check_folder)

    if args.upload_folder and args.destination_folder:
        oci_storage.bulk_upload_to_folder(args.upload_folder, args.destination_folder)

    if args.delete_folder:
        oci_storage.bulk_delete(args.delete_folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCI Storage Management")
    parser.add_argument("--list-files", action="store_true", help="List all files in the bucket")
    parser.add_argument("--check-folder", metavar="FOLDER", help="Check if a folder exists in the bucket")
    parser.add_argument("--upload-folder", metavar="UPLOAD_FOLDER", help="Local folder to upload files from")
    parser.add_argument("--destination-folder", metavar="DESTINATION_FOLDER", help="Destination folder in the bucket")
    parser.add_argument("--delete-folder", metavar="DELETE_FOLDER", help="Folder to delete files from in the bucket")

    args = parser.parse_args()
    main(args)
