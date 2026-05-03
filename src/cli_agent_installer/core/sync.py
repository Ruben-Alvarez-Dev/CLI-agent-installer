"""File synchronization with zombie removal for CLI-agent-installer.

Handles:
- Clean file synchronization from source to destination
- Detection and removal of zombie files (files not in manifest payload)
- Preservation of user data (files in manifest preserve)
- Dry-run mode for testing
"""

import fnmatch
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Set
from .manifest import Manifest


class SyncManager:
    """Manages file synchronization with zombie removal."""

    def __init__(self, source_dir: Path, dest_dir: Path, manifest: Manifest):
        """Initialize SyncManager.

        Args:
            source_dir: Source directory (e.g., downloaded tarball)
            dest_dir: Destination directory (installation dir)
            manifest: Manifest object with payload/preserve patterns
        """
        self.source_dir = Path(source_dir)
        self.dest_dir = Path(dest_dir)
        self.manifest = manifest

    def sync(self, dry_run: bool = False) -> Tuple[int, int, List[str]]:
        """Perform sync operation.

        Args:
            dry_run: If True, only report what would be done

        Returns:
            Tuple of (files_copied, files_deleted, zombies)
        """
        # 1. Collect files from source (payload)
        source_files = self._collect_payload_files()

        # 2. Collect files in destination
        dest_files = self._collect_dest_files()

        # 3. Detect zombies (files in dest but not in source)
        zombies = self._detect_zombies(source_files, dest_files)

        # 4. Delete zombies
        files_deleted = 0
        for zombie in zombies:
            if dry_run:
                files_deleted += 1
            else:
                if zombie.exists():
                    if zombie.is_file():
                        zombie.unlink()
                        files_deleted += 1
                    elif zombie.is_dir():
                        shutil.rmtree(zombie)
                        files_deleted += 1

        # 5. Copy new/modified files
        files_copied = 0
        for source_file in source_files:
            rel_path = source_file.relative_to(self.source_dir)
            dest_file = self.dest_dir / rel_path

            # Check if file needs to be copied
            if not dest_file.exists() or self._file_changed(source_file, dest_file):
                if dry_run:
                    files_copied += 1
                else:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    if source_file.is_file():
                        shutil.copy2(source_file, dest_file)
                        files_copied += 1
                    elif source_file.is_dir():
                        dest_file.mkdir(exist_ok=True)
                        files_copied += 1

        return (files_copied, files_deleted, [str(z) for z in zombies])

    def _collect_payload_files(self) -> Set[Path]:
        """Collect all files matching payload patterns from source.

        Returns:
            Set of file paths
        """
        files = set()
        for pattern in self.manifest.payload:
            # Handle patterns like "src/**", "README.md"
            if "**" in pattern:
                # Recursive glob (rglob is equivalent to **/*)
                for file in self.source_dir.rglob("*"):
                    if file.is_file():
                        files.add(file)
            else:
                # Simple glob (non-recursive)
                for file in self.source_dir.glob(pattern):
                    if file.is_file():
                        files.add(file)
        return files

    def _collect_dest_files(self) -> Set[Path]:
        """Collect all files in destination directory.

        Returns:
            Set of file paths
        """
        files = set()
        if not self.dest_dir.exists():
            return files

        for file in self.dest_dir.rglob("*"):
            if file.is_file():
                files.add(file)
        return files

    def _detect_zombies(
        self, source_files: Set[Path], dest_files: Set[Path]
    ) -> List[Path]:
        """Detect files in destination that are not in source (zombies).

        Args:
            source_files: Files from source (payload)
            dest_files: Files in destination

        Returns:
            List of zombie files to delete
        """
        zombies = []

        # Create set of relative paths from source
        source_rel = {f.relative_to(self.source_dir) for f in source_files}

        for dest_file in dest_files:
            rel_path = dest_file.relative_to(self.dest_dir)

            # Check if file is in preserve patterns
            if self._is_preserved(rel_path):
                continue

            # Check if file is in source
            if rel_path not in source_rel:
                zombies.append(dest_file)

        return zombies

    def _is_preserved(self, rel_path: Path) -> bool:
        """Check if a path matches any preserve pattern.

        Args:
            rel_path: Relative path from dest_dir

        Returns:
            True if path should be preserved
        """
        path_str = str(rel_path)
        for pattern in self.manifest.preserve:
            if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(
                path_str, pattern.replace("**", "*")
            ):
                return True
        return False

    def _file_changed(self, source: Path, dest: Path) -> bool:
        """Check if file has changed.

        Args:
            source: Source file
            dest: Destination file

        Returns:
            True if file needs to be updated
        """
        if source.is_file() and dest.is_file():
            # Compare modification times and sizes
            return (
                source.stat().st_mtime > dest.stat().st_mtime
                or source.stat().st_size != dest.stat().st_size
            )
        return True
