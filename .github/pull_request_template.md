# Pull Request: Release v0.2.0 - Video to MP3 Conversion and Enhanced Logging

## Summary

This PR introduces ✨ new features for video to MP3 conversion and enhanced logging capabilities, along with 💎 style improvements for better user experience. It includes changes to core functionality, logging system, and user interface components.

---

## Files Changed

### Added
1. **`subber/utils/converter.py`**  
   - ✨ New module for video to MP3 conversion functionality using ffmpeg
2. **`subber_logs/.gitkeep`**  
   - 📦 Directory for storing application logs

### Modified
1. **`subber/cli/main.py`**  
   - ✨ Added MP3 conversion command-line options
   - 💎 Enhanced console output with rich formatting
   - 📝 Improved error messages and user feedback

2. **`subber/utils/file_ops.py`**  
   - ✨ Added "Select All" option for batch operations
   - ♻️ Improved file operation handling and feedback
   - 💎 Added progress bars for file operations

3. **`subber/utils/logging.py`**  
   - ✨ Implemented comprehensive logging system
   - 📝 Added configurable log levels and file output

4. **`requirements.txt`**  
   - 📦 Added better-ffmpeg-progress>=1.1.0 dependency

5. **`pyproject.toml`**  
   - 📦 Updated project configuration and dependencies

6. **`setup.py`** and **`subber/__init__.py`**  
   - 📦 Bumped version to 0.2.0

---

## Code Changes

### `subber/utils/converter.py`
```python
def convert_to_mp3(video_file: Path, output_dir: Path) -> bool:
    """Convert a video file to MP3 format using ffmpeg."""
    try:
        output_path = output_dir / f"{video_file.stem}.mp3"
        cmd = [
            'ffmpeg',
            '-i', str(video_file),
            '-q:a', '0',
            '-map', 'a',
            '-y',
            str(output_path)
        ]
        ff = FfmpegProcess(cmd, ffmpeg_log_level="error")
        return_code = ff.run()
        return return_code == 0
    except Exception as e:
        logger.error(f"Failed to convert {video_file.name}")
        return False
```

- Added new converter module with ffmpeg integration for MP3 conversion
- Implemented progress tracking and error handling
- Added user-friendly console output with rich formatting

---

## Reason for Changes

- Adding video to MP3 conversion feature to expand tool functionality
- Improving user experience with better feedback and progress indicators
- Enhancing debugging capabilities with comprehensive logging
- Making the codebase more maintainable with better error handling and documentation

---

## Impact of Changes

### Positive Impacts
- Users can now convert video files to MP3 format
- Better visibility into operation progress with progress bars
- Improved error handling and user feedback
- Enhanced debugging capabilities with detailed logging
- More intuitive batch operations with "Select All" option

### Potential Issues
- Requires ffmpeg to be installed for MP3 conversion
- Increased disk usage due to log files
- Potential performance impact from additional logging

---

## Test Plan

1. **Unit Testing**  
   - Tested MP3 conversion functionality
   - Verified logging system configuration
   - Tested file operations with various scenarios
   - Validated error handling paths

2. **Integration Testing**  
   - Tested interaction between file operations and logging
   - Verified MP3 conversion with different video formats
   - Tested batch operations with multiple files

3. **Manual Testing**  
   - Verified MP3 conversion quality
   - Tested progress bars and console output
   - Validated logging output and file structure
   - Tested "Select All" functionality
   - Verified error messages and user feedback

---

## Additional Notes

- Log files are stored in `subber_logs` directory with timestamps
- Consider adding log rotation in future updates
- May want to add configuration options for MP3 quality settings
- Consider adding parallel processing for batch conversions 