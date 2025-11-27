#!/usr/bin/env python3
"""
LeetCode FSRS CLI 主程序入口
基于FSRS记忆算法的LeetCode刷题工具
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import cli


if __name__ == "__main__":
    cli()