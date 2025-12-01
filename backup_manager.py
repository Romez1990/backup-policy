from pathlib import Path
from datetime import datetime
import re
import logging

from data import BackupFile, RetentionPolicy
from retention_policy_applier import RetentionPolicyApplier


class BackupManager:
    """
    Manages backup files according to retention policies.
    """

    def __init__(self, retention_policy: list[RetentionPolicy], backup_dir: str) -> None:
        self._backup_dir = Path(backup_dir)
        self._file_pattern = re.compile(r'.*\.(zip)$')
        self._backup_files: list[BackupFile] = []
        self._logger = logging.getLogger(__name__)
        self._policy_applier = RetentionPolicyApplier(self._logger, retention_policy)


    def run_cleanup(self, dry_run: bool = False) -> None:
        """Execute the complete backup cleanup process."""
        self._logger.info('Starting backup cleanup process')

        self._scan_backups()
        self._apply_retention_policies()

        if dry_run:
            self._dry_run()
            return
        deleted_count = self._cleanup_old_backups()
        self._logger.info(f'Cleanup completed. Deleted {deleted_count} files')

    def _scan_backups(self) -> None:
        """Scan backup directory and parse backup files."""
        self._backup_files.clear()

        if not self._backup_dir.exists():
            self._logger.error(f'Backup directory {self._backup_dir} does not exist')
            return

        for file_path in self._backup_dir.iterdir():
            if not file_path.is_file() or not self._file_pattern.match(file_path.name):
                continue
            timestamp = self._parse_timestamp_from_filename(file_path)
            if timestamp is None:
                continue
            self._backup_files.append(BackupFile(file_path, timestamp))

        # Sort by timestamp (newest first)
        self._logger.info(f'Found {len(self._backup_files)} backup files')

    def _parse_timestamp_from_filename(self, file_path: Path) -> datetime:
        """
        Parse timestamp from filename.
        Supports common formats: backup_20231215_123045.zip, backup_2023-12-15_12-30-45.sql, etc.
        """
        filename = file_path.stem
        pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})')  # 2023-12-15-12-30-45
        match = re.search(pattern, filename)
        if match:
            try:
                year, month, day, hour, minute, second = map(int, match.groups())
                return datetime(year, month, day, hour, minute, second)
            except ValueError:
                pass

        # If no pattern matches, use file modification time
        self._logger.warning(f"Could not parse timestamp from {file_path.name}, using modification time")
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    def _apply_retention_policies(self) -> None:
        """Apply retention policies to mark which backups to keep."""
        self._policy_applier.apply(self._backup_files)
        
        # Log retention plan
        to_delete = sum(1 for b in self._backup_files if b.should_delete)
        kept = len(self._backup_files) - to_delete
        self._logger.info(f"Retention plan: {kept} to keep, {to_delete} to delete")

    def _cleanup_old_backups(self) -> int:
        """
        Delete backups marked for removal.

        Returns:
            Number of deleted files
        """
        for backup in self._backup_files:
            if not backup.should_delete:
                continue
            try:
                backup.file_path.unlink()  # Delete file
            except OSError as e:
                self._logger.error(f"Failed to delete {backup.file_path.name}: {e}")
                continue
            self._logger.info(f"Deleted old backup: {backup.file_path.name}")
        return sum(1 for b in self._backup_files if b.should_delete)

    def _dry_run(self) -> None:
        """Simulate cleanup without actually deleting files."""
        self._logger.info("=== DRY RUN MODE ===")

        if not self._backup_files:
            self._logger.info("No backup files found")
            return

        self._logger.info("Backups to KEEP:")
        for backup in sorted(self._backup_files, key=lambda x: x.timestamp, reverse=True):
            if not backup.should_delete:
                self._logger.info(f"  KEEP: {backup.file_path.name} - {backup.timestamp}")

        self._logger.info("Backups to DELETE:")
        for backup in sorted(self._backup_files, key=lambda x: x.timestamp, reverse=True):
            if not not backup.should_delete:
                self._logger.info(f"  DELETE: {backup.file_path.name} - {backup.timestamp}")

        total_size = sum(b.file_path.stat().st_size for b in self._backup_files if b.should_delete)
        self._logger.info(f"Total space to free: {total_size / (1024 ** 3):.2f} GB")
