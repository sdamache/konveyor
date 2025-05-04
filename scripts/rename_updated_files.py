#!/usr/bin/env python
"""
Script to rename the updated files to replace the originals.

This script renames the updated files to replace the originals,
creating backups of the original files.
"""

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def rename_files():
    """Rename the updated files to replace the originals."""
    logger.info("Renaming updated files to replace originals...")

    # Create a backup directory
    backup_dir = (
        project_root / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    backup_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created backup directory: {backup_dir}")

    # Define the files to rename
    files_to_rename = [
        ("konveyor/core/chat/skill_updated.py", "konveyor/core/chat/skill.py"),
        (
            "konveyor/core/rag/rag_service_updated.py",
            "konveyor/core/rag/rag_service.py",
        ),
        ("konveyor/apps/bot/views_updated.py", "konveyor/apps/bot/views.py"),
        ("konveyor/apps/rag/views_updated.py", "konveyor/apps/rag/views.py"),
    ]

    # Rename the files
    for updated_file, original_file in files_to_rename:
        updated_path = project_root / updated_file
        original_path = project_root / original_file
        backup_path = backup_dir / original_file

        # Create the backup directory structure
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if the files exist
        if not updated_path.exists():
            logger.warning(f"Updated file not found: {updated_path}")
            continue

        if not original_path.exists():
            logger.warning(f"Original file not found: {original_path}")
        else:
            # Backup the original file
            logger.info(f"Backing up {original_path} to {backup_path}")
            shutil.copy2(original_path, backup_path)

        # Rename the updated file
        logger.info(f"Renaming {updated_path} to {original_path}")
        shutil.copy2(updated_path, original_path)

    logger.info("File renaming completed!")
    logger.info(f"Original files backed up to: {backup_dir}")


if __name__ == "__main__":
    rename_files()
