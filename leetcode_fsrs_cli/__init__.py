"""
LeetCode FSRS CLI - 基于FSRS算法的LeetCode刷题工具

项目架构说明:
- cli.py: CLI交互界面 (基于Click框架)
- fsrs.py: FSRS算法核心实现
- leetcode.py: 题目管理和数据结构
- scheduler.py: 复习调度和优先级计算
- storage.py: 数据持久化 (JSON存储)

数据流:
1. 用户输入 → cli.py → 命令解析
2. 算法计算 → fsrs.py → 记忆间隔
3. 题目管理 → leetcode.py → 题目数据
4. 调度逻辑 → scheduler.py → 复习计划
5. 数据存储 → storage.py → JSON文件

维护信息:
- 项目状态: 已完成并发布到AUR
- 版本: 1.5.0
- 最后维护: 2025-11-28
- 维护记录: 详见项目根目录的MAINTENANCE_LOG.md
"""

__version__ = "1.5.0"
__author__ = "SaintFore"
__email__ = "saintfore@example.com"

# 导出主要类和函数供外部使用
from .cli import LeetCodeFSRSCLI, cli
from .fsrs import FSRS, ReviewRecord
from .leetcode import QuestionManager, Question
from .scheduler import ReviewScheduler, ReviewSession
from .storage import StorageManager

__all__ = [
    'LeetCodeFSRSCLI',
    'cli',
    'FSRS',
    'ReviewRecord',
    'QuestionManager',
    'Question',
    'ReviewScheduler',
    'ReviewSession',
    'StorageManager'
]