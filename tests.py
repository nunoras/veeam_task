import unittest
import os
import shutil
import tempfile
import sys
from sync_folders import synchronize_folders, backup_files
import time
import threading
from unittest.mock import patch


class TestSyncFolders(unittest.TestCase):
    def setUp(self):
        # Create temporary source, replica and backup folders
        self.source_folder = tempfile.mkdtemp()
        self.replica_folder = tempfile.mkdtemp()
        self.backup_folder = tempfile.mkdtemp()

        # Create some files in the source folder
        for i in range(5):
            with open(os.path.join(self.source_folder, f"file_{i}.txt"), "w") as f:
                f.write(f"Content of file {i}")

        # Create some files in the backup folder
        for i in range(3):
            with open(os.path.join(self.backup_folder, f"backup_file_{i}.txt"), "w") as f:
                f.write(f"Content of backup file {i}")

    def tearDown(self):
        # Remove temporary folders
        shutil.rmtree(self.source_folder)
        shutil.rmtree(self.replica_folder)
        shutil.rmtree(self.backup_folder)
    
    def test_synchronize_folders_empty_source(self):
        # Delete all files in the source folder
        for filename in os.listdir(self.source_folder):
            file_path = os.path.join(self.source_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Assert that the replica folder remains empty
        self.assertEqual(len(os.listdir(self.replica_folder)), 0)

    def test_synchronize_folders_replica_not_created(self):
        # Remove replica folder if it exists
        if os.path.exists(self.replica_folder):
            shutil.rmtree(self.replica_folder)

        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Assert that the replica folder has been created
        self.assertTrue(os.path.exists(self.replica_folder))

        # Assert that all files from the source folder have been copied to the replica folder
        source_files = set(os.listdir(self.source_folder))
        replica_files = set(os.listdir(self.replica_folder))
        self.assertSetEqual(source_files, replica_files)

    def test_synchronize_folders(self):
        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Check if files are copied correctly
        for i in range(5):
            source_file = os.path.join(self.source_folder, f"file_{i}.txt")
            replica_file = os.path.join(self.replica_folder, f"file_{i}.txt")
            self.assertTrue(os.path.exists(replica_file))
            with open(source_file, "r") as src, open(replica_file, "r") as rep:
                self.assertEqual(src.read(), rep.read())

    def test_synchronize_folders_with_existing_files(self):
        # Copy some files to the replica folder
        for i in range(3):
            shutil.copy2(os.path.join(self.source_folder,
                         f"file_{i}.txt"), self.replica_folder)

        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Check if files are copied correctly
        for i in range(5):
            source_file = os.path.join(self.source_folder, f"file_{i}.txt")
            replica_file = os.path.join(self.replica_folder, f"file_{i}.txt")
            self.assertTrue(os.path.exists(replica_file))
            with open(source_file, "r") as src, open(replica_file, "r") as rep:
                self.assertEqual(src.read(), rep.read())

    def test_synchronize_folders_nested_source(self):
        # Create nested source folder structure
        os.makedirs(os.path.join(self.source_folder, "subdir1"))
        os.makedirs(os.path.join(self.source_folder, "subdir2"))

        # Create files within subdirectories
        for i in range(3):
            with open(os.path.join(self.source_folder, "subdir1", f"file_{i}.txt"), "w") as f:
                f.write(f"Content of file {i} in subdir1")
        for i in range(3):
            with open(os.path.join(self.source_folder, "subdir2", f"file_{i}.txt"), "w") as f:
                f.write(f"Content of file {i} in subdir2")

        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Verify files in replica folder
        replica_files = []
        for root, _, files in os.walk(self.replica_folder):
            for file in files:
                replica_files.append(os.path.relpath(
                    os.path.join(root, file), self.replica_folder))

        expected_files = [
            "file_0.txt",
            "file_1.txt",
            "file_2.txt",
            "file_3.txt",
            "file_4.txt",
            "subdir1\\file_0.txt",
            "subdir1\\file_1.txt",
            "subdir1\\file_2.txt",
            "subdir2\\file_0.txt",
            "subdir2\\file_1.txt",
            "subdir2\\file_2.txt",
        ]

        self.maxDiff = None
        self.assertCountEqual(replica_files, expected_files)

    def test_synchronize_folders_file_deletion(self):
        # Perform synchronization to copy files to the replica folder
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Delete some files from the source folder
        for i in range(2):
            os.remove(os.path.join(self.source_folder, f"file_{i}.txt"))

        # Perform synchronization again to reflect the changes
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Verify that deleted files are removed from the replica folder
        replica_files = os.listdir(self.replica_folder)
        expected_files = [f"file_{i}.txt" for i in range(2, 5)]
        self.assertCountEqual(replica_files, expected_files)

    def test_synchronize_folders_replica_file_deletion(self):
        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Delete some files from the replica folder
        deleted_files = []
        for i in range(2):
            file_path = os.path.join(self.replica_folder, f"file_{i}.txt")
            os.remove(file_path)
            deleted_files.append(file_path)

        # Perform synchronization again to reflect the changes
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Verify that deleted files are restored in the replica folder
        for file_path in deleted_files:
            self.assertTrue(os.path.exists(
                file_path), f"File {file_path} should be restored in the replica folder")

    def test_synchronize_folders_file_modification_in_source(self):
        # Create a file in the source folder
        file_path = os.path.join(self.source_folder, "file_5.txt")
        with open(file_path, "w") as f:
            f.write("Initial content")

        # Perform initial synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Modify the file in the source folder
        with open(file_path, "w") as f:
            f.write("Modified content")

        # Perform synchronization again
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Verify that the modified file is updated in the replica folder
        replica_file_path = os.path.join(self.replica_folder, "file_5.txt")
        with open(replica_file_path, "r") as f:
            content = f.read()
            self.assertEqual(content, "Modified content")

    def test_synchronize_folders_file_modification_in_replica(self):
        # Create a file in the source folder
        file_content_source = "Initial content"
        file_path_source = os.path.join(self.source_folder, "file_5.txt")
        with open(file_path_source, "w") as f:
            f.write(file_content_source)

        # Create a file with different content in the replica folder
        file_content_replica = "Replica content"
        file_path_replica = os.path.join(self.replica_folder, "file_5.txt")
        with open(file_path_replica, "w") as f:
            f.write(file_content_replica)

        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Verify that the content of the file in the replica folder is overwritten
        with open(file_path_replica, "r") as f:
            content = f.read()
            self.assertEqual(content, file_content_source)

    def test_synchronize_folders_large_files(self):
        # Example usage:
        large_file_path = os.path.join(self.source_folder, f"large_file.txt")
        with open(large_file_path, "wb") as f:
            f.write(b'\0' * (100 * 1024 * 1024))  # 100Mb

        # Perform synchronization and measure the time taken
        start_time = time.time()
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")
        end_time = time.time()

        # Verify that the large file is correctly synchronized
        replica_large_file_path = os.path.join(
            self.replica_folder, "large_file.txt")
        self.assertTrue(os.path.exists(replica_large_file_path))

        # Print the time taken for synchronization
        print(
            f"Time taken for synchronization with large file: {end_time - start_time} seconds")

    def test_synchronize_folders_special_characters_in_filenames(self):
        # Create files with special characters in the source folder
        # Add more special filenames as needed
        special_file_names = [
            "file with spaces.txt", "file_with_ㄴéé_unicode.txt"]
        for filename in special_file_names:
            file_path = os.path.join(self.source_folder, filename)
            with open(file_path, "w") as f:
                f.write("Content")

        # Perform synchronization
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")

        # Verify that files with special characters are correctly synchronized
        for filename in special_file_names:
            replica_file_path = os.path.join(self.replica_folder, filename)
            self.assertTrue(os.path.exists(replica_file_path))

    def test_synchronize_folders_performance(self):
        # Create additional files in the source folder
        for i in range(95):
            with open(os.path.join(self.source_folder, f"file_{i + 4}.txt"), "w") as f:
                f.write(f"Content of file {i + 5}")

        start_time = time.time()
        synchronize_folders(self.source_folder,
                            self.replica_folder, "test.log")
        end_time = time.time()

        # Calculate the time taken for synchronization
        sync_time = end_time - start_time

        # Print the time taken for synchronization
        print(f"Time taken for synchronization: {sync_time} seconds")

        # Assert that synchronization takes less than 5 seconds
        self.assertLess(sync_time, 5, "Synchronization took too long")

    def test_concurrent_access(self):
        num_threads = 5
        threads = []

        def synchronize():
            synchronize_folders(self.source_folder,
                                self.replica_folder, "test.log")

        # Create and start multiple threads for synchronization
        for _ in range(num_threads):
            thread = threading.Thread(target=synchronize)
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Ensure that synchronization completes without errors
        self.assertTrue(all(thread.is_alive() == False for thread in threads))


if __name__ == "__main__":
    unittest.main(buffer=False)
