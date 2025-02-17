# Subber

A command-line tool for matching video files with their corresponding subtitle files. Subber helps you organize your media library by finding exact and close matches between video files and subtitle files, with options to rename and organize unmatched files.

## Table of Contents

- [Badges](#badges)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)
- [Contributing](#contributing)

## Badges

![Python](https://img.shields.io/badge/Python-3.6%2B-blue)
![Version](https://img.shields.io/badge/version-0.2.0-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- Recursively scans directories for video files (.mkv, .mov, .mp4) and subtitle files (.srt)
- Finds exact matches based on filenames
- Identifies close matches using filename similarity
- Interactive subtitle file renaming
- Option to move unmatched video files to a separate directory
- Colorful and clear output formatting
- Export results to a text file

## Installation

### Option 1: Using pipx (Recommended)

```bash
pipx install "git+https://github.com/beecave-homelab/subber.git"
```

### Option 2: Using virtualenv (For development)

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Clone and install
git clone https://github.com/beecave-homelab/subber.git
cd subber
pip install -r requirements.txt
```

## Usage

There are two ways to run Subber:

1. As a command-line tool:
```bash
subber -d /path/to/your/media/folder
```

2. As a Python module:
```bash
python -m subber -d /path/to/your/media/folder
```

Available options:

```
Options:
  -d, --directory TEXT     Directory to search for files  [default: .]
  -o, --output-file TEXT   File path to save the output
  -n, --no-table          Output results without table formatting
  -p, --path              Show the full path of the files in the output
  -m, --move-unmatched TEXT  Folder to move unmatched video files into
  -r, --rename            Interactively rename close-matched subtitle files
  --help                  Show this message and exit
```

### Examples

1. Search in current directory with table output:
```bash
subber
# or
python -m subber
```

2. Search in specific directory and show full paths:
```bash
subber -d /media/movies -p
```

3. Search, rename close matches, and move unmatched:
```bash
subber -d /media/movies -r -m unmatched
```

4. Export results to a file:
```bash
subber -d /media/movies -o results.txt
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for more information.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
