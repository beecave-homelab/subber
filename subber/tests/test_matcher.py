"""
Tests for the matcher module.
"""

import unittest
from pathlib import Path
from datetime import datetime
from ..core.matcher import (
    extract_date,
    normalize_filename,
    collect_files,
    find_matches,
    InvalidPathError
)

class TestMatcher(unittest.TestCase):
    """Test cases for the matcher module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_files")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create some test files
        (self.test_dir / "video1.mp4").touch()
        (self.test_dir / "video1.srt").touch()
        (self.test_dir / "video2_2024-01-24.mp4").touch()
        (self.test_dir / "video2_24.01.24.srt").touch()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_extract_date(self):
        """Test date extraction from filenames."""
        # Test YYYY-MM-DD format
        self.assertEqual(
            extract_date("video_2024-01-24.mp4"),
            datetime(2024, 1, 24)
        )
        
        # Test DD.MM.YY format
        self.assertEqual(
            extract_date("video_24.01.24.mp4"),
            datetime(2024, 1, 24)
        )
        
        # Test no date
        self.assertIsNone(extract_date("video.mp4"))
    
    def test_normalize_filename(self):
        """Test filename normalization."""
        path = Path("Test.File-Name_123.mp4")
        expected = {"test", "file", "name", "123"}
        self.assertEqual(normalize_filename(path), expected)
        
        # Test invalid path
        with self.assertRaises(InvalidPathError):
            normalize_filename(None)
    
    def test_collect_files(self):
        """Test file collection."""
        videos, subs = collect_files(self.test_dir)
        
        self.assertEqual(len(videos), 2)
        self.assertEqual(len(subs), 2)
        
        # Test invalid directory
        with self.assertRaises(InvalidPathError):
            collect_files(Path("nonexistent"))
    
    def test_find_matches(self):
        """Test file matching."""
        videos, subs = collect_files(self.test_dir)
        
        exact, close, unmatched = find_matches(videos, subs)
        
        # Should find one exact match (video1)
        self.assertEqual(len(exact), 1)
        self.assertEqual(exact[0][0].stem, "video1")
        
        # Should find one close match (video2 with date)
        self.assertEqual(len(close), 1)
        self.assertTrue("video2" in close[0][0].stem)
        
        # Should have no unmatched videos
        self.assertEqual(len(unmatched), 0)
        
        # Test invalid similarity threshold
        with self.assertRaises(ValueError):
            find_matches(videos, subs, min_similarity=2.0)

if __name__ == '__main__':
    unittest.main() 