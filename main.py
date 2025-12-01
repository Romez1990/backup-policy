from argparse import ArgumentParser

from config import backup_retention_policy
from backup_manager import BackupManager
from setup_logging import setup_logging


def main():
    """Main function with example usage."""
    setup_logging()

    parser = ArgumentParser(description='Backup retention manager')
    parser.add_argument('--backup-dir', required=True, help='Backup directory path')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without deleting')
    args = parser.parse_args()

    manager = BackupManager(backup_retention_policy, args.backup_dir)
    manager.run_cleanup(dry_run=args.dry_run)


if __name__ == '__main__':
    main()