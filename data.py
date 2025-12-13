from dataclasses import dataclass, field
from datetime import timedelta, datetime
from pathlib import Path


@dataclass
class RetentionPolicy:
    """
    Class describing backup retention policy.

    Attributes:
        interval: Time interval between backups
        keep_count: Number of backups to keep
    """
    interval: timedelta
    keep_count: int


@dataclass
class BackupFile:
    """Represents a backup file with its timestamp and retention status."""

    file_path: Path
    timestamp: datetime
    _should_delete: bool = field(default=False, init=False)

    def mark_to_delete(self) -> None:
        """Mark this backup to be deleted."""
        self._should_delete = True

    @property
    def should_delete(self) -> bool:
        """Check if this backup should be deleted."""
        return self._should_delete
