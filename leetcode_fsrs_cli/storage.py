"""
数据持久化模块
负责复习记录和用户配置的存储
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .fsrs import ReviewRecord


class StorageManager:
    """存储管理器"""

    def __init__(self, data_dir: str = None):
        # 使用 XDG 标准目录
        if data_dir is None:
            xdg_config_home = os.environ.get('XDG_CONFIG_HOME',
                                           os.path.expanduser('~/.config'))
            self.data_dir = Path(xdg_config_home) / "leetcode-fsrs-cli"
        else:
            self.data_dir = Path(data_dir)

        self.reviews_file = self.data_dir / "reviews.json"
        self.config_file = self.data_dir / "config.json"
        self.questions_file = self.data_dir / "questions.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # 复习记录相关方法

    def load_reviews(self) -> Dict[int, ReviewRecord]:
        """
        加载复习记录

        Returns:
            Dict[int, ReviewRecord]: 复习记录字典
        """
        if not os.path.exists(self.reviews_file):
            return {}

        try:
            with open(self.reviews_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            reviews = {}
            for qid_str, review_data in data.items():
                try:
                    review = ReviewRecord.from_dict(review_data)
                    reviews[int(qid_str)] = review
                except (KeyError, ValueError) as e:
                    print(f"加载题目 {qid_str} 的复习记录失败: {e}")

            return reviews

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"加载复习记录失败: {e}")
            return {}

    def save_reviews(self, reviews: Dict[int, ReviewRecord]):
        """
        保存复习记录

        Args:
            reviews: 复习记录字典
        """
        data = {
            str(qid): review.to_dict()
            for qid, review in reviews.items()
        }

        try:
            with open(self.reviews_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存复习记录失败: {e}")

    def get_review_record(self, question_id: int) -> Optional[ReviewRecord]:
        """
        获取指定题目的复习记录

        Args:
            question_id: 题目ID

        Returns:
            Optional[ReviewRecord]: 复习记录，如果不存在返回None
        """
        reviews = self.load_reviews()
        return reviews.get(question_id)

    def save_review_record(self, review: ReviewRecord):
        """
        保存单个复习记录

        Args:
            review: 复习记录对象
        """
        reviews = self.load_reviews()
        reviews[review.question_id] = review
        self.save_reviews(reviews)

    def delete_review_record(self, question_id: int) -> bool:
        """
        删除指定题目的复习记录

        Args:
            question_id: 题目ID

        Returns:
            bool: 是否成功删除
        """
        reviews = self.load_reviews()
        if question_id not in reviews:
            return False

        del reviews[question_id]
        self.save_reviews(reviews)
        return True

    # 配置相关方法

    def load_config(self) -> dict:
        """
        加载用户配置

        Returns:
            dict: 配置字典
        """
        default_config = {
            "daily_review_limit": 20,
            "auto_update_due": True,
            "show_progress_bar": True,
            "language": "zh",
            "fsrs_params": {
                "request_retention": 0.9,
                "maximum_interval": 36500,
                "easy_bonus": 1.3,
                "hard_factor": 1.2
            }
        }

        if not os.path.exists(self.config_file):
            return default_config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)

            # 合并默认配置和用户配置
            merged_config = default_config.copy()
            merged_config.update(user_config)
            return merged_config

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"加载配置失败: {e}")
            return default_config

    def save_config(self, config: dict):
        """
        保存用户配置

        Args:
            config: 配置字典
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def update_config(self, updates: dict):
        """
        更新配置

        Args:
            updates: 要更新的配置项
        """
        config = self.load_config()
        config.update(updates)
        self.save_config(config)

    # 统计相关方法

    def get_review_stats(self) -> dict:
        """
        获取复习统计信息

        Returns:
            dict: 统计信息
        """
        reviews = self.load_reviews()
        now = datetime.now()

        total_reviews = len(reviews)
        due_reviews = sum(1 for r in reviews.values()
                         if r.next_review and r.next_review <= now)

        # 按难度统计
        difficulty_stats = {"easy": 0, "medium": 0, "hard": 0}
        for review in reviews.values():
            # 这里需要从题目管理器获取难度信息
            # 暂时使用稳定性作为难度参考
            if review.difficulty <= 3:
                difficulty_stats["easy"] += 1
            elif review.difficulty <= 6:
                difficulty_stats["medium"] += 1
            else:
                difficulty_stats["hard"] += 1

        # 平均稳定性
        avg_stability = (
            sum(r.stability for r in reviews.values()) / total_reviews
            if total_reviews > 0 else 0
        )

        return {
            "total_reviews": total_reviews,
            "due_reviews": due_reviews,
            "difficulty_stats": difficulty_stats,
            "avg_stability": avg_stability
        }

    def get_due_reviews(self) -> List[ReviewRecord]:
        """
        获取到期的复习记录

        Returns:
            List[ReviewRecord]: 到期的复习记录列表
        """
        reviews = self.load_reviews()
        now = datetime.now()

        due_reviews = [
            review for review in reviews.values()
            if review.next_review and review.next_review <= now
        ]

        # 按下次复习时间排序
        due_reviews.sort(key=lambda r: r.next_review)
        return due_reviews

    def backup_data(self, backup_dir: str = "backup") -> bool:
        """
        备份数据

        Args:
            backup_dir: 备份目录

        Returns:
            bool: 是否成功备份
        """
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 备份复习记录
            if os.path.exists(self.reviews_file):
                backup_file = os.path.join(backup_dir, f"reviews_{timestamp}.json")
                with open(self.reviews_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())

            # 备份配置
            if os.path.exists(self.config_file):
                backup_file = os.path.join(backup_dir, f"config_{timestamp}.json")
                with open(self.config_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())

            return True

        except Exception as e:
            print(f"备份数据失败: {e}")
            return False