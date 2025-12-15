from datetime import datetime
from itertools import count
from queue import Queue
from typing import Iterable

from data import BackupFile, RetentionPolicy


class RetentionPolicyApplier:
    """Handles the application of retention policies to backup files."""

    def __init__(self, logger, retention_policies: list[RetentionPolicy]) -> None:
        """Initialize the RetentionPolicyApplier.
        
        Args:
            logger: Logger instance for logging messages
            backup_files: List of BackupFile objects to process
            retention_policies: List of RetentionPolicy objects to apply
        """
        self._logger = logger
        self._retention_policies = retention_policies
        self._backup_queue: Queue[BackupFile] = Queue()
        self._last_backup_datetime: datetime | None = None

    def apply(self, backups: Iterable[BackupFile]) -> None:
        """Apply all retention policies to the backup files."""
        self._initialize_backup_queue(backups)

        if not self._backup_queue:
            self._logger.info('No backup files to process')
            return

        for policy in self._retention_policies:
            self._apply_single_policy(policy)

    def _initialize_backup_queue(self, backups: Iterable[BackupFile]) -> None:
        """Initialize the backup queue with sorted backup files.

        Args:
            backups: Iterable of BackupFile objects to process
        """
        if not self._backup_queue.empty():
            self._logger.warning('Queue must be empty')
            self._backup_queue.queue.clear()
        for backup in sorted(backups, key=lambda backup: backup.timestamp, reverse=True):
            self._backup_queue.put_nowait(backup)
        self._last_backup_datetime = None

    def _apply_single_policy(self, policy: RetentionPolicy) -> None:
        """Apply a single retention policy.
        
        Args:
            policy: The retention policy to apply
        """
        is_last_policy = policy is self._retention_policies[-1]
        for _ in range(policy.keep_count) if not is_last_policy else count(0):
            backup = self._find_backup_to_keep(policy)
            if backup is None:
                break
            self._last_backup_datetime = backup.timestamp

    def _find_backup_to_keep(self, policy: RetentionPolicy) -> BackupFile | None:
        min_interval = self._retention_policies[0].interval

        while not self._backup_queue.empty():
            backup = self._backup_queue.get_nowait()
            is_newest_backup = self._last_backup_datetime is None
            if is_newest_backup:
                return backup

            intervals_past = (self._last_backup_datetime - backup.timestamp) / min_interval
            required_intervals_to_pass = policy.interval / min_interval
            if round(intervals_past) < round(required_intervals_to_pass):
                backup.mark_to_delete()
                continue
            return backup

        return None
