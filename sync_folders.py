import os
import sys
import time
import shutil
import hashlib
import logging
import tempfile

def log_and_print(message, level=logging.INFO):
    """Print a message to the console and log it with the specified level."""
    print(message)
    if level == logging.INFO:
        logging.info(message)
    elif level == logging.ERROR:
        logging.error(message)


def calculate_md5(filename, block_size=65536):
    """Calculate the MD5 checksum of a file."""
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            md5.update(block)
    return md5.hexdigest()


def backup_files(source_dir, backup_dir):
    """Backup files from the source directory to the backup directory."""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    for root, _, files in os.walk(source_dir):
        for file in files:
            source_file = os.path.join(root, file)
            backup_file = os.path.join(
                backup_dir, os.path.relpath(source_file, source_dir))
            os.makedirs(os.path.dirname(backup_file), exist_ok=True)
            shutil.copy2(source_file, backup_file)

    print(f"Files backed up from {source_dir} to {backup_dir}")


def synchronize_folders(source, replica, log_file):
    """Synchronize the source folder to the replica folder."""

    log_and_print("Synchronization started")

    try:
        # Create temporary directory for rollback & backup files before synchronization
        temp_dir = tempfile.mkdtemp()
        backup_files(replica, temp_dir)

        # Walk through the source folder
        for root, _, files in os.walk(source):
            for file in files:
                source_file = os.path.join(root, file)
                replica_file = os.path.join(
                    replica, os.path.relpath(source_file, source))

                # Create directories in replica if they don't exist
                replica_parent_dir = os.path.dirname(replica_file)
                if not os.path.exists(replica_parent_dir):
                    os.makedirs(replica_parent_dir)

                if not os.path.exists(replica_file) or \
                        calculate_md5(source_file) != calculate_md5(replica_file):
                    log_and_print(f"Copying {source_file} to {replica_file}")
                    shutil.copy2(source_file, replica_file)

        # Remove files in replica that don't exist in source
        for root, _, files in os.walk(replica):
            for file in files:
                replica_file = os.path.join(root, file)
                source_file = os.path.join(
                    source, os.path.relpath(replica_file, replica))

                if not os.path.exists(source_file):
                    log_and_print(
                        f"Removing {replica_file} from {replica}")
                    os.remove(replica_file)

        log_and_print("Synchronization completed")

    except Exception as e:
        log_and_print(
            f"An error occurred during synchronization: {e}", level=logging.ERROR)
        logging.error(f"Error during synchronization: {e}")

        # Rollback changes from backup directory
        log_and_print("Rolling back changes...")
        for root, _, files in os.walk(temp_dir):
            for file in files:
                temp_file = os.path.join(root, file)
                replica_file = os.path.join(
                    replica, os.path.relpath(temp_file, temp_dir))

                # Restore file from backup directory
                if os.path.exists(replica_file):
                    os.remove(replica_file)
                shutil.copy2(temp_file, replica_file)

        log_and_print("Rollback completed")

    finally:
        # Cleanup temporary directory
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python sync_folders.py <source_folder> <replica_folder> <sync_interval_minutes> <log_file>")
        sys.exit(1)

    source_folder = sys.argv[1]
    replica_folder = sys.argv[2]
    sync_interval = int(sys.argv[3]) * 60  # Convert sync interval to seconds
    log_file = sys.argv[4]

    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(message)s')

    if not os.path.isdir(source_folder) or not os.path.isdir(replica_folder):
        log_and_print(
            "Source and replica folders must be valid directories.", level=logging.ERROR)
        sys.exit(1)
    
    if source_folder == replica_folder:
        log_and_print(
            "Source and replica folders can't be the same.", level=logging.ERROR)
        sys.exit(1)

    while True:
        try:
            synchronize_folders(
                source_folder, replica_folder, log_file)
            time.sleep(sync_interval)  # Synchronize every specified interval
        except KeyboardInterrupt:
            log_and_print("Synchronization interrupted by user.")
            sys.exit(0)
