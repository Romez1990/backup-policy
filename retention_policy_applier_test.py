import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

from data import BackupFile, RetentionPolicy
from retention_policy_applier import RetentionPolicyApplier

real_backup_names = [
    ('2025-12-01-03-39-17.zip', True),
    ('2025-12-01-03-24-17.zip', True),
    ('2025-12-01-03-09-17.zip', False),
    ('2025-12-01-02-54-17.zip', False),
    ('2025-12-01-02-39-17.zip', False),
    ('2025-12-01-02-24-17.zip', True),
    ('2025-12-01-02-09-17.zip', False),
    ('2025-12-01-01-54-17.zip', False),
    ('2025-12-01-01-39-17.zip', False),
    ('2025-12-01-01-24-17.zip', True),
    ('2025-12-01-01-09-17.zip', False),
    ('2025-12-01-00-54-17.zip', False),
    ('2025-12-01-00-39-17.zip', False),
    ('2025-12-01-00-24-17.zip', True),
    ('2025-12-01-00-09-17.zip', False),
    ('2025-11-30-23-54-17.zip', False),
    ('2025-11-30-23-39-17.zip', False),
    ('2025-11-30-23-24-16.zip', False),
    ('2025-11-30-23-09-16.zip', False),
    ('2025-11-30-22-54-16.zip', False),
    ('2025-11-30-22-39-16.zip', False),
    ('2025-11-30-21-39-04.zip', False),
    ('2025-11-30-21-24-04.zip', False),
    ('2025-11-30-21-09-04.zip', False),
    ('2025-11-30-20-54-04.zip', False),
    ('2025-11-30-20-03-56.zip', True),
    ('2025-11-30-19-48-56.zip', False),
    ('2025-11-30-19-33-56.zip', False),
    ('2025-11-30-19-08-46.zip', False),
    ('2025-11-30-18-53-46.zip', False),
    ('2025-11-30-18-38-46.zip', False),
    ('2025-11-30-08-51-14.zip', True),
    ('2025-11-30-08-36-14.zip', False),
]


@pytest.fixture
def real_backups() -> list[BackupFile]:
    """Fixture that provides a list of BackupFile objects for testing."""
    return [
        BackupFile(Path(name), datetime.strptime(Path(name).stem, '%Y-%m-%d-%H-%M-%S'))
        for name, _ in real_backup_names
    ]


def test_retention_policy_applier(real_backups: list[BackupFile]) -> None:
    """Test that retention policies are correctly applied to backup files."""
    retention_policy = [
        RetentionPolicy(interval=timedelta(minutes=15), keep_count=2),
        RetentionPolicy(interval=timedelta(hours=1), keep_count=3),
        RetentionPolicy(interval=timedelta(hours=4), keep_count=2),
        RetentionPolicy(interval=timedelta(days=1), keep_count=7),
    ]
    mock_logger = Mock()
    applier = RetentionPolicyApplier(logger=mock_logger, retention_policies=retention_policy)
    
    applier.apply(real_backups)

    backups_to_delete = [backup for backup in real_backups if backup.should_delete]
    backups_to_keep = [backup for backup in real_backups if not backup.should_delete]
    
    # Basic assertions
    assert len(backups_to_keep) > 0, "Expected to keep some backups"
    assert len(backups_to_delete) > 0, "Expected to mark some backups for deletion"
    assert len(backups_to_keep) < len(real_backups), "Expected to delete some backups"
    
    # Verify the most recent backup is kept
    most_recent_backup = max(real_backups, key=lambda x: x.timestamp)
    assert not most_recent_backup.should_delete, "Most recent backup should be kept"
    
    # Verify we have the expected number of backups kept
    max_expected_kept = 2 + 3 + 2 + 7  # Sum of all keep_counts
    assert len(backups_to_keep) <= max_expected_kept, f"Should keep at most {max_expected_kept} backups"
    
    # Verify that kept backups are spaced according to policies
    kept_timestamps = sorted([b.timestamp for b in backups_to_keep], reverse=True)
    
    # Group timestamps by policy ranges
    policy_ranges = [
        (0, 2, timedelta(minutes=10)),    # First 2 should be ~15 minutes apart
        (2, 5, timedelta(minutes=45)),    # Next 3 should be ~1 hour apart
        (5, 7, timedelta(hours=3)),       # Next 2 should be ~4 hours apart
        (7, None, timedelta(hours=20))    # Rest should be ~1 day apart
    ]
    
    for i in range(1, len(kept_timestamps)):
        time_diff = kept_timestamps[i-1] - kept_timestamps[i]
        
        # Find which policy range this backup falls into
        for start, end, min_interval in policy_ranges:
            if (end is None and i >= start) or (start <= i < end):
                assert time_diff >= min_interval, (
                    f"Backup at position {i} should be at least {min_interval} after the previous one, "
                    f"but is only {time_diff} apart"
                )
                break

    result = [(backup.file_path.name, not backup.should_delete) for backup in real_backups]
    assert result == real_backup_names
