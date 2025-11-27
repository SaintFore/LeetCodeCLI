#!/usr/bin/env python3
"""
Setup script for LeetCode FSRS CLI

项目包配置说明:
- 包名: leetcode-fsrs-cli
- 版本: 1.1.0
- 描述: 基于FSRS间隔重复算法的LeetCode刷题CLI工具
- 依赖: 见requirements.txt (已优化，仅保留必需依赖)
- 入口点: leetcode-fsrs 命令

维护信息:
- 项目状态: 已完成并发布到AUR (双版本策略)
- 最后维护: 2025-11-28
- 维护记录: 详见MAINTENANCE_LOG.md

注意:
- 更新版本时需要同时更新PKGBUILD文件
- 依赖变更需要更新requirements.txt
- 包数据包含data目录下的JSON配置文件
- 提供源码版和二进制版双版本策略
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
    version="1.1.0",
    author="SaintFore",
    author_email="saintfore@example.com",
    description="A CLI tool for LeetCode practice using FSRS spaced repetition algorithm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SaintFore/LeetCodeCLI",
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