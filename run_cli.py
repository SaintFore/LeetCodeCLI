import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from leetcode_fsrs_cli.cli import cli

if __name__ == '__main__':
    cli()
