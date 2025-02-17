"""
Subber is a tool for matching video files with subtitle files.
"""

from setuptools import setup, find_packages

# Read the content of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="subber",
    version="0.2.0",
    author="elvee",
    description="A tool for matching video files with subtitle files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/beecave-homelab/subber",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "questionary>=2.0.0",
        "rapidfuzz>=3.0.0",
        "tabulate>=0.9.0",
        "better-ffmpeg-progress>=1.1.0",
    ],
    entry_points={
        "console_scripts": [
            "subber=subber.cli.main:main",
        ],
    },
)
