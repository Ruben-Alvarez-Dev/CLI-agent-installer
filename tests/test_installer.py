"""Tests for CLI-agent-installer."""

import json
import tempfile
from pathlib import Path

import pytest

from cli_agent_installer.core import VersionManager, ManifestManager, SyncManager, Manifest


class TestManifest:
    """Test Manifest operations."""

    def test_manifest_load_not_found(self):
        """Test loading manifest when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ManifestManager(Path(tmpdir))
            manifest = manager.load()
            assert manifest is None

    def test_manifest_save_and_load(self):
        """Test saving and loading manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ManifestManager(Path(tmpdir))
            manifest = Manifest(
                version="1.0.0",
                repo="owner/project",
                python_min="3.12",
                payload=["src/**"],
                preserve=["data/**"],
            )

            assert manager.save(manifest) is True
            loaded = manager.load()
            assert loaded is not None
            assert loaded.version == "1.0.0"
            assert loaded.repo == "owner/project"

    def test_manifest_generate_template(self):
        """Test generating manifest template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ManifestManager(Path(tmpdir))
            manifest = manager.generate_template(repo="owner/project", version="2.0.0")

            assert manifest.version == "2.0.0"
            assert manifest.repo == "owner/project"
            assert len(manifest.payload) > 0
            assert len(manifest.preserve) > 0


class TestVersionManager:
    """Test VersionManager operations."""

    def test_get_local_version_unknown(self):
        """Test getting version when manifest doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = VersionManager(Path(tmpdir))
            assert manager.get_local_version() == "unknown"

    def test_get_local_version(self):
        """Test getting version from manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest_dir = tmpdir / "install"
            manifest_dir.mkdir()
            manifest_path = manifest_dir / "manifest.json"
            manifest_path.write_text(json.dumps({"version": "3.0.0"}))

            manager = VersionManager(tmpdir)
            assert manager.get_local_version() == "3.0.0"

    def test_bump_version(self):
        """Test bumping version in manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest_dir = tmpdir / "install"
            manifest_dir.mkdir()
            manifest_path = manifest_dir / "manifest.json"
            manifest_path.write_text(json.dumps({"version": "1.0.0", "repo": "owner/project"}))

            manager = VersionManager(tmpdir)
            assert manager.bump_version("2.0.0") is True

            # Verify version changed
            with open(manifest_path) as f:
                data = json.load(f)
            assert data["version"] == "2.0.0"


class TestSyncManager:
    """Test SyncManager operations."""

    def test_sync_no_changes(self):
        """Test sync with no changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source"
            dest = tmpdir / "dest"

            # Create source files
            source.mkdir()
            (source / "test.txt").write_text("content")
            (source / "subdir").mkdir()
            (source / "subdir" / "file.txt").write_text("sub")

            # Create identical dest
            dest.mkdir()
            (dest / "test.txt").write_text("content")
            (dest / "subdir").mkdir()
            (dest / "subdir" / "file.txt").write_text("sub")

            manifest = Manifest(
                version="1.0.0",
                repo="owner/project",
                payload=["**"],
                preserve=[".preserve/**"],
            )

            sync = SyncManager(source, dest, manifest)
            copied, deleted, zombies = sync.sync()

            # Directory creation counts as copy
            # No changes means no copies or deletions
            assert copied == 0
            assert deleted == 0
            assert len(zombies) == 0

    def test_sync_new_files(self):
        """Test sync with new files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source"
            dest = tmpdir / "dest"

            # Create source files
            source.mkdir()
            (source / "new.txt").write_text("new content")

            # Empty dest
            dest.mkdir()

            manifest = Manifest(
                version="1.0.0", repo="owner/project", payload=["*"], preserve=[]
            )

            sync = SyncManager(source, dest, manifest)
            copied, deleted, zombies = sync.sync()

            assert copied > 0
            assert (dest / "new.txt").exists()

    def test_sync_zombie_removal(self):
        """Test sync removes zombie files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source"
            dest = tmpdir / "dest"

            # Empty source
            source.mkdir()

            # Dest has zombie
            dest.mkdir()
            (dest / "zombie.txt").write_text("old file")

            manifest = Manifest(
                version="1.0.0", repo="owner/project", payload=["*"], preserve=[]
            )

            sync = SyncManager(source, dest, manifest)
            copied, deleted, zombies = sync.sync()

            assert deleted > 0
            assert not (dest / "zombie.txt").exists()
            assert "zombie.txt" in str(zombies)

    def test_sync_preserve_files(self):
        """Test sync preserves files in preserve patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source"
            dest = tmpdir / "dest"

            # Empty source
            source.mkdir()

            # Dest has data that should be preserved
            dest.mkdir()
            data_dir = dest / "data"
            data_dir.mkdir()
            (data_dir / "user.json").write_text("important data")

            manifest = Manifest(
                version="1.0.0",
                repo="owner/project",
                payload=["*"],
                preserve=["data/**"],
            )

            sync = SyncManager(source, dest, manifest)
            copied, deleted, zombies = sync.sync()

            assert deleted == 0  # Should not delete preserved files
            assert (dest / "data" / "user.json").exists()  # Data preserved
