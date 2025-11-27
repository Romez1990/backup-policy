from dataclasses import dataclass
from datetime import timedelta


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
