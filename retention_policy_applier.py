from datetime import datetime
from logging import Logger

from data import BackupFile, RetentionPolicy


class RetentionPolicyApplier:
    """Handles the application of retention policies to backup files."""

    def __init__(self, logger: Logger, backup_files: list[BackupFile], retention_policies: list[RetentionPolicy]) -> None:
        """Initialize the RetentionPolicyApplier.
        
        Args:
            logger: Logger instance for logging messages
            backup_files: List of BackupFile objects to process
            retention_policies: List of RetentionPolicy objects to apply
        """
        self.logger = logger
        self.backup_files = backup_files.copy()
        self.retention_policies = retention_policies

    def apply(self) -> None:
        """Apply all retention policies to the backup files."""
        if not self.backup_files:
            self.logger.info("No backup files to process")
            return

        for policy in self.retention_policies:
            self._apply_single_policy(policy)

    def _apply_single_policy(self, policy: RetentionPolicy, current_time: datetime) -> None:
        """Apply a single retention policy."""
        kept_count = 0
        last_kept_time = current_time

        # Go through backups from newest to oldest
        for backup in sorted(self.backup_files, key=lambda x: x.timestamp, reverse=True):
            if kept_count >= policy.keep_count:
                break

            # If backup is already kept by a previous policy, skip it
            if backup._keep:
                continue

            # Check if this backup fits the interval
            time_diff = last_kept_time - backup.timestamp
            if time_diff >= policy.interval:
                backup.mark_to_keep()
                kept_count += 1
                last_kept_time = backup.timestamp
                self.logger.debug(f"Keeping {backup.file_path.name} (policy: {policy.interval})")
