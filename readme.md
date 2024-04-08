# Sync Folders

Sync Folders is a Python script that synchronizes the contents of two folders. It compares the files in a source folder with those in a replica folder and ensures that they are identical.

## Features

- Copies new and updated files from the source folder to the replica folder.
- Deletes files from the replica folder if they are not present in the source folder.
- Supports logging to track synchronization operations.
- Implements rollback functionality in case of errors during synchronization.

## Installation

Clone the repository:

```bash
git clone https://github.com/nunoras/sync-folders.git
```

Usage
Run the script with the following command:

```bash
python sync_folders.py <source_folder> <replica_folder> <sync_interval_minutes> <log_file>
```
Replace <source_folder>, <replica_folder>, <sync_interval_minutes>, and <log_file> with the appropriate values.

<source_folder>: The path to the source folder.
<replica_folder>: The path to the replica folder.
<sync_interval_minutes>: The synchronization interval in minutes.
<log_file>: The path to the log file for logging synchronization activities.

Tests
To run the unit tests, use the following command:

```bash
python -m unittest tests.py
```