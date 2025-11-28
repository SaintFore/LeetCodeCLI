"""
LeetCode题目管理模块
负责题目的存储、检索和管理
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Question:
    """LeetCode题目数据结构"""
    id: int
    title: str
    difficulty: str  # "easy", "medium", "hard"
    tags: List[str]
    url: str
    content: str = ""

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "url": self.url,
            "content": self.content
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建实例"""
        return cls(
            id=data["id"],
            title=data["title"],
            difficulty=data["difficulty"],
            tags=data["tags"],
            url=data["url"],
            content=data.get("content", "")
        )


class QuestionManager:
    """题目管理器"""

    def __init__(self, data_dir: str = None):
        # 使用 XDG 标准目录
        if data_dir is None:
            xdg_config_home = os.environ.get('XDG_CONFIG_HOME',
                                           os.path.expanduser('~/.config'))
            self.data_dir = Path(xdg_config_home) / "leetcode-fsrs-cli"
        else:
            self.data_dir = Path(data_dir)

        self.questions_file = self.data_dir / "questions.json"
        self.questions: Dict[int, Question] = {}
        self._ensure_data_dir()
        self._load_questions()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_questions(self):
        """从文件加载题目数据"""
        if os.path.exists(self.questions_file):
            try:
                with open(self.questions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.questions = {
                        int(qid): Question.from_dict(q_data)
                        for qid, q_data in data.items()
                    }
            except (json.JSONDecodeError, KeyError) as e:
                print(f"加载题目数据失败: {e}")
                self.questions = {}

    def _save_questions(self):
        """保存题目数据到文件"""
        data = {
            str(qid): question.to_dict()
            for qid, question in self.questions.items()
        }
        with open(self.questions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_question(self, question: Question) -> bool:
        """
        添加题目

        Args:
            question: 题目对象

        Returns:
            bool: 是否成功添加
        """
        if question.id in self.questions:
            return False

        self.questions[question.id] = question
        self._save_questions()
        return True

    def get_question(self, question_id: int) -> Optional[Question]:
        """
        获取题目

        Args:
            question_id: 题目ID

        Returns:
            Optional[Question]: 题目对象，如果不存在返回None
        """
        return self.questions.get(question_id)

    def remove_question(self, question_id: int) -> bool:
        """
        移除题目

        Args:
            question_id: 题目ID

        Returns:
            bool: 是否成功移除
        """
        if question_id not in self.questions:
            return False

        del self.questions[question_id]
        self._save_questions()
        return True

    def list_questions(
        self,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Question]:
        """
        列出题目

        Args:
            difficulty: 难度过滤
            tags: 标签过滤

        Returns:
            List[Question]: 题目列表
        """
        questions = list(self.questions.values())

        if difficulty:
            questions = [q for q in questions if q.difficulty == difficulty]

        if tags:
            questions = [
                q for q in questions
                if any(tag in q.tags for tag in tags)
            ]

        return sorted(questions, key=lambda q: q.id)

    def search_questions(self, keyword: str) -> List[Question]:
        """
        搜索题目

        Args:
            keyword: 搜索关键词

        Returns:
            List[Question]: 匹配的题目列表
        """
        keyword = keyword.lower()
        return [
            q for q in self.questions.values()
            if (keyword in q.title.lower() or
                keyword in str(q.id) or
                any(keyword in tag.lower() for tag in q.tags))
        ]

    def get_question_count_by_difficulty(self) -> Dict[str, int]:
        """
        按难度统计题目数量

        Returns:
            Dict[str, int]: 难度-数量映射
        """
        counts = {"easy": 0, "medium": 0, "hard": 0}
        for question in self.questions.values():
            diff = question.difficulty.lower()
            if diff in counts:
                counts[diff] += 1
            else:
                # Handle unknown difficulty if necessary, or just ignore
                pass
        return counts

    def import_from_file(self, file_path: str) -> int:
        """
        从文件导入题目

        Args:
            file_path: 文件路径

        Returns:
            int: 成功导入的题目数量
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_count = 0
            for q_data in data:
                question = Question.from_dict(q_data)
                if self.add_question(question):
                    imported_count += 1

            return imported_count

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"导入题目失败: {e}")
            return 0

    def export_to_file(self, file_path: str) -> bool:
        """
        导出题目到文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否成功导出
        """
        try:
            data = [question.to_dict() for question in self.questions.values()]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出题目失败: {e}")
            return False


# 预定义的一些示例题目
SAMPLE_QUESTIONS = [
    Question(
        id=1,
        title="Two Sum",
        difficulty="easy",
        tags=["array", "hash-table"],
        url="https://leetcode.com/problems/two-sum/",
        content="给定一个整数数组 nums 和一个目标值 target..."
    ),
    Question(
        id=2,
        title="Add Two Numbers",
        difficulty="medium",
        tags=["linked-list", "math"],
        url="https://leetcode.com/problems/add-two-numbers/",
        content="给你两个非空的链表，表示两个非负的整数..."
    ),
    Question(
        id=3,
        title="Longest Substring Without Repeating Characters",
        difficulty="medium",
        tags=["hash-table", "two-pointers", "string"],
        url="https://leetcode.com/problems/longest-substring-without-repeating-characters/",
        content="给定一个字符串，请你找出其中不含有重复字符的最长子串的长度..."
    ),
    Question(
        id=4,
        title="Median of Two Sorted Arrays",
        difficulty="hard",
        tags=["array", "binary-search", "divide-and-conquer"],
        url="https://leetcode.com/problems/median-of-two-sorted-arrays/",
        content="给定两个大小分别为 m 和 n 的正序（从小到大）数组 nums1 和 nums2..."
    )
]