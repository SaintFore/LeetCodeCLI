"""
FSRS (Free Spaced Repetition Scheduler) 算法实现
基于FSRS v4算法，用于计算最优复习间隔
"""

import math
from datetime import datetime, timedelta
from typing import Tuple, List


class FSRS:
    """FSRS记忆算法核心类"""

    def __init__(self, params: dict = None):
        """
        初始化FSRS算法

        Args:
            params: FSRS算法参数，如果为None则使用默认参数
        """
        self.params = params or self.get_default_params()

    @staticmethod
    def get_default_params() -> dict:
        """获取FSRS默认参数"""
        return {
            "w": [
                0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01,
                1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61
            ],
            "request_retention": 0.9,  # 目标记忆保留率
            "maximum_interval": 36500,  # 最大间隔天数
            "easy_bonus": 1.3,  # 简单题目奖励
            "hard_factor": 1.2   # 困难题目惩罚
        }

    def next_interval(
        self,
        stability: float,
        difficulty: float,
        rating: int,
        elapsed_days: float
    ) -> Tuple[float, float, float]:
        """
        计算下一次复习间隔

        Args:
            stability: 当前记忆稳定性
            difficulty: 当前题目难度
            rating: 用户评分 (1-5)
            elapsed_days: 距离上次复习的天数

        Returns:
            Tuple[new_stability, new_difficulty, new_interval]
        """
        w = self.params["w"]

        if rating == 1:  # 忘记
            new_difficulty = self._constrain_difficulty(difficulty + w[15])
            new_stability = w[16] * math.pow(difficulty, w[17]) * math.pow(new_difficulty, -w[18])
            new_interval = 1
        else:
            # 计算回忆成功率
            retrievability = math.pow(1 + elapsed_days / (9 * stability), -1)

            # 更新难度
            new_difficulty = self._constrain_difficulty(
                difficulty + w[7] * (rating - 3)
            )

            # 更新稳定性
            if rating == 2:  # 困难
                new_stability = w[9] * math.pow(difficulty, w[10]) * math.pow(new_difficulty, -w[11]) * stability
            elif rating == 3:  # 中等
                new_stability = w[12] * math.pow(difficulty, w[13]) * math.pow(new_difficulty, -w[14]) * stability
            else:  # 简单或完美
                new_stability = stability * (1 + w[5] * (5 - rating) * math.pow(retrievability, w[6]))

            # 计算新间隔
            if rating == 2:  # 困难
                new_interval = elapsed_days * self.params["hard_factor"]
            elif rating == 4:  # 简单
                new_interval = elapsed_days * self.params["easy_bonus"]
            else:  # 中等或完美
                new_interval = elapsed_days * (1 + w[4] * (rating - 3))

            # 应用间隔约束
            new_interval = max(1, min(new_interval, self.params["maximum_interval"]))

        return new_stability, new_difficulty, new_interval

    def _constrain_difficulty(self, difficulty: float) -> float:
        """约束难度值在合理范围内"""
        return max(1, min(10, difficulty))

    def calculate_next_review(
        self,
        current_time: datetime,
        stability: float,
        difficulty: float,
        rating: int,
        last_review: datetime
    ) -> Tuple[datetime, float, float]:
        """
        计算下一次复习时间

        Args:
            current_time: 当前时间
            stability: 当前记忆稳定性
            difficulty: 当前题目难度
            rating: 用户评分 (1-5)
            last_review: 上次复习时间

        Returns:
            Tuple[next_review_time, new_stability, new_difficulty]
        """
        elapsed_days = (current_time - last_review).total_seconds() / (24 * 3600)

        new_stability, new_difficulty, new_interval = self.next_interval(
            stability, difficulty, rating, elapsed_days
        )

        next_review = current_time + timedelta(days=new_interval)

        return next_review, new_stability, new_difficulty

    def get_initial_state(self) -> Tuple[float, float]:
        """获取初始状态（新题目）"""
        return 2.5, 5.0  # 初始稳定性，初始难度


class ReviewRecord:
    """复习记录类"""

    def __init__(self, question_id: int):
        self.question_id = question_id
        self.review_history = []
        self.stability = 2.5  # 初始稳定性
        self.difficulty = 5.0  # 初始难度
        self.next_review = None
        self.due = False

    def add_review(
        self,
        timestamp: datetime,
        rating: int,
        fsrs: FSRS
    ):
        """
        添加复习记录

        Args:
            timestamp: 复习时间
            rating: 用户评分 (1-5)
            fsrs: FSRS算法实例
        """
        last_review = self.review_history[-1]["timestamp"] if self.review_history else timestamp

        next_review, new_stability, new_difficulty = fsrs.calculate_next_review(
            timestamp, self.stability, self.difficulty, rating, last_review
        )

        review_data = {
            "timestamp": timestamp,
            "rating": rating,
            "stability": self.stability,
            "difficulty": self.difficulty,
            "interval": (next_review - timestamp).days
        }

        self.review_history.append(review_data)
        self.stability = new_stability
        self.difficulty = new_difficulty
        self.next_review = next_review
        self.due = False

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "question_id": self.question_id,
            "review_history": [
                {
                    "timestamp": review["timestamp"].isoformat(),
                    "rating": review["rating"],
                    "stability": review["stability"],
                    "difficulty": review["difficulty"],
                    "interval": review["interval"]
                }
                for review in self.review_history
            ],
            "stability": self.stability,
            "difficulty": self.difficulty,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "due": self.due
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建实例"""
        record = cls(data["question_id"])
        record.review_history = [
            {
                "timestamp": datetime.fromisoformat(review["timestamp"]),
                "rating": review["rating"],
                "stability": review["stability"],
                "difficulty": review["difficulty"],
                "interval": review["interval"]
            }
            for review in data["review_history"]
        ]
        record.stability = data["stability"]
        record.difficulty = data["difficulty"]
        record.next_review = (
            datetime.fromisoformat(data["next_review"])
            if data["next_review"] else None
        )
        record.due = data["due"]
        return record