from datetime import timedelta

from data import RetentionPolicy

backup_retention_policy = [
    RetentionPolicy(interval=timedelta(minutes=15), keep_count=2),
    RetentionPolicy(interval=timedelta(minutes=30), keep_count=2),
    RetentionPolicy(interval=timedelta(hours=1), keep_count=2),
    RetentionPolicy(interval=timedelta(hours=2), keep_count=2),
    RetentionPolicy(interval=timedelta(hours=6), keep_count=2),
    RetentionPolicy(interval=timedelta(days=1), keep_count=3),
    RetentionPolicy(interval=timedelta(days=3), keep_count=2),
    RetentionPolicy(interval=timedelta(weeks=1), keep_count=4),
]
