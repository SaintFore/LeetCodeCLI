#!/usr/bin/env python3
"""
Setup script for LeetCode FSRS CLI
"""

from setuptools import setup, find_packages
import os

# 读取 README.md 作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取 requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="leetcode-fsrs-cli",
    version="1.0.0",
    author="Julien",
    author_email="your-email@example.com",
    description="A CLI tool for LeetCode practice using FSRS spaced repetition algorithm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/leetcode-fsrs-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "leetcode-fsrs=leetcode_fsrs_cli.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["data/*.json"],
    },
    data_files=[
        ('share/leetcode-fsrs-cli', ['README.md', 'LICENSE']),
    ],
)