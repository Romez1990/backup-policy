import logging
import re
from datetime import datetime
from pathlib import Path

from data import BackupFile, RetentionPolicy
from retention_policy_applier import RetentionPolicyApplier
from config import backup_retention_policy


class BackupManager:
    """
    Manages backup files according to retention policies.
    """

    def __init__(self, backup_dir: str, file_pattern: str = r".*\.(zip|tar|gz|sql)$"):
        self.backup_dir = Path(backup_dir)
        self.file_pattern = re.compile(file_pattern)
        self.backup_files: list[BackupFile] = []

        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/backup_cleaner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def scan_backups(self) -> None:
        """Scan backup directory and parse backup files."""
        self.backup_files.clear()

        if not self.backup_dir.exists():
            self.logger.error(f"Backup directory {self.backup_dir} does not exist")
            return

        for file_path in self.backup_dir.iterdir():
            if file_path.is_file() and self.file_pattern.match(file_path.name):
                timestamp = self._parse_timestamp_from_filename(file_path)
                if timestamp:
                    self.backup_files.append(BackupFile(file_path, timestamp))

        # Sort by timestamp (newest first)
        self.backup_files.sort(key=lambda x: x.timestamp, reverse=True)
        self.logger.info(f"Found {len(self.backup_files)} backup files")

    def _parse_timestamp_from_filename(self, file_path: Path) -> datetime | None:
        """
        Parse timestamp from filename.
        Supports common formats: backup_20231215_123045.zip, backup_2023-12-15_12-30-45.sql, etc.
        """
        filename = file_path.stem  # Get filename without extension

        # Try different timestamp patterns
        patterns = [
            r'(\d{4})(\d{2})(\d{2})_?(\d{2})(\d{2})(\d{2})',  # 20231215_123045
            r'(\d{4})-?(\d{2})-?(\d{2})_?(\d{2})-?(\d{2})-?(\d{2})',  # 2023-12-15_12-30-45
            r'(\d{4})\.?(\d{2})\.?(\d{2})_?(\d{2})\.?(\d{2})\.?(\d{2})',  # 2023.12.15_12.30.45
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    year, month, day, hour, minute, second = map(int, match.groups())
                    return datetime(year, month, day, hour, minute, second)
                except ValueError:
                    continue

        # If no pattern matches, use file modification time
        self.logger.warning(f"Could not parse timestamp from {file_path.name}, using modification time")
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    def apply_retention_policies(self) -> None:
        """Apply retention policies to mark which backups to keep."""
        if not self.backup_files:
            self.logger.info("No backup files to process")
            return

        # Mark all for deletion initially
        for backup in self.backup_files:
            backup._keep = False

        # Apply each retention policy
        current_time = datetime.now()

        retention_policies = RetentionPolicyApplier(self.logger, self.backup_files, backup_retention_policy)
        retention_policies.apply()

        # Log retention plan
        kept = sum(1 for b in self.backup_files if b._keep)
        to_delete = sum(1 for b in self.backup_files if not b._keep)
        self.logger.info(f"Retention plan: {kept} to keep, {to_delete} to delete")

    def cleanup_old_backups(self) -> int:
        """
        Delete backups marked for removal.

        Returns:
            Number of deleted files
        """
        deleted_count = 0

        for backup in self.backup_files:
            if backup.should_delete():
                try:
                    backup.file_path.unlink()  # Delete file
                    self.logger.info(f"Deleted old backup: {backup.file_path.name}")
                    deleted_count += 1
                except OSError as e:
                    self.logger.error(f"Failed to delete {backup.file_path.name}: {e}")

        return deleted_count

    def dry_run(self) -> None:
        """Simulate cleanup without actually deleting files."""
        self.logger.info("=== DRY RUN MODE ===")

        if not self.backup_files:
            self.logger.info("No backup files found")
            return

        self.logger.info("Backups to KEEP:")
        for backup in sorted(self.backup_files, key=lambda x: x.timestamp, reverse=True):
            if backup._keep:
                self.logger.info(f"  KEEP: {backup.file_path.name} - {backup.timestamp}")

        self.logger.info("Backups to DELETE:")
        for backup in sorted(self.backup_files, key=lambda x: x.timestamp, reverse=True):
            if not backup._keep:
                self.logger.info(f"  DELETE: {backup.file_path.name} - {backup.timestamp}")

        total_size = sum(b.file_path.stat().st_size for b in self.backup_files if not b._keep)
        self.logger.info(f"Total space to free: {total_size / (1024 ** 3):.2f} GB")

    def run_cleanup(self, dry_run: bool = False) -> None:
        """Execute the complete backup cleanup process."""
        self.logger.info("Starting backup cleanup process")

        self.scan_backups()
        self.apply_retention_policies()

        if dry_run:
            self.dry_run()
        else:
            deleted_count = self.cleanup_old_backups()
            self.logger.info(f"Cleanup completed. Deleted {deleted_count} files")