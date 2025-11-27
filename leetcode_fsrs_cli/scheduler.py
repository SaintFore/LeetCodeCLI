"""
复习调度器
负责生成复习计划和安排复习顺序
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .fsrs import FSRS, ReviewRecord
from .leetcode import Question


@dataclass
class ReviewSession:
    """复习会话"""
    question: Question
    review_record: ReviewRecord
    priority: float  # 优先级分数，用于排序


class ReviewScheduler:
    """复习调度器"""

    def __init__(self, fsrs: FSRS):
        self.fsrs = fsrs

    def generate_daily_review_plan(
        self,
        due_reviews: List[ReviewRecord],
        questions: Dict[int, Question],
        limit: int = 20
    ) -> List[ReviewSession]:
        """
        生成每日复习计划

        Args:
            due_reviews: 到期的复习记录
            questions: 题目字典
            limit: 每日复习题目数量限制

        Returns:
            List[ReviewSession]: 复习会话列表
        """
        sessions = []

        for review in due_reviews:
            question = questions.get(review.question_id)
            if question:
                priority = self._calculate_priority(review, question)
                session = ReviewSession(question, review, priority)
                sessions.append(session)

        # 按优先级排序
        sessions.sort(key=lambda s: s.priority, reverse=True)

        # 限制数量
        return sessions[:limit]

    def _calculate_priority(self, review: ReviewRecord, question: Question) -> float:
        """
        计算复习优先级

        Args:
            review: 复习记录
            question: 题目

        Returns:
            float: 优先级分数
        """
        now = datetime.now()

        # 基础优先级：距离下次复习时间越近，优先级越高
        time_priority = 0.0
        if review.next_review:
            days_overdue = (now - review.next_review).total_seconds() / (24 * 3600)
            time_priority = max(0, days_overdue)

        # 难度权重：难度越高，优先级越高
        difficulty_weights = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
        difficulty_weight = difficulty_weights.get(question.difficulty, 1.0)

        # 稳定性权重：稳定性越低，优先级越高
        stability_weight = max(0.1, 5.0 - review.stability)

        # 复习次数权重：复习次数越多，优先级越低（避免过度复习）
        review_count = len(review.review_history)
        review_weight = max(0.5, 1.0 - review_count * 0.1)

        # 综合优先级
        priority = (
            time_priority * 2.0 +
            difficulty_weight * 1.5 +
            stability_weight * 1.0 +
            review_weight * 0.5
        )

        return priority

    def get_review_suggestions(
        self,
        all_questions: List[Question],
        reviewed_questions: List[int],
        limit: int = 5
    ) -> List[Question]:
        """
        获取新题目建议

        Args:
            all_questions: 所有题目
            reviewed_questions: 已复习的题目ID列表
            limit: 建议数量限制

        Returns:
            List[Question]: 建议的新题目列表
        """
        # 过滤未复习的题目
        new_questions = [
            q for q in all_questions
            if q.id not in reviewed_questions
        ]

        # 按难度和标签多样性排序
        def get_question_score(question: Question) -> float:
            difficulty_scores = {"easy": 1.0, "medium": 2.0, "hard": 3.0}
            return difficulty_scores.get(question.difficulty, 1.0)

        new_questions.sort(key=get_question_score)

        # 确保题目类型多样性
        selected_questions = []
        selected_tags = set()

        for question in new_questions:
            if len(selected_questions) >= limit:
                break

            # 检查是否有新的标签
            new_tags = set(question.tags) - selected_tags
            if new_tags or not selected_questions:
                selected_questions.append(question)
                selected_tags.update(question.tags)

        # 如果还不够，补充剩余的题目
        if len(selected_questions) < limit:
            remaining = [q for q in new_questions if q not in selected_questions]
            selected_questions.extend(remaining[:limit - len(selected_questions)])

        return selected_questions

    def calculate_review_progress(
        self,
        sessions: List[ReviewSession],
        completed_count: int
    ) -> Dict[str, float]:
        """
        计算复习进度

        Args:
            sessions: 复习会话列表
            completed_count: 已完成复习数量

        Returns:
            Dict[str, float]: 进度统计
        """
        total_count = len(sessions)
        if total_count == 0:
            return {
                "completion_rate": 0.0,
                "remaining_count": 0,
                "estimated_time": 0.0
            }

        completion_rate = completed_count / total_count
        remaining_count = total_count - completed_count

        # 估计剩余时间（假设每题平均5分钟）
        estimated_time = remaining_count * 5

        return {
            "completion_rate": completion_rate,
            "remaining_count": remaining_count,
            "estimated_time": estimated_time
        }

    def get_study_analytics(
        self,
        review_records: List[ReviewRecord],
        time_period: int = 30  # 天
    ) -> Dict[str, any]:
        """
        获取学习分析

        Args:
            review_records: 复习记录列表
            time_period: 分析的时间周期（天）

        Returns:
            Dict[str, any]: 分析数据
        """
        now = datetime.now()
        cutoff_date = now - timedelta(days=time_period)

        # 过滤指定时间范围内的复习记录
        recent_reviews = []
        for record in review_records:
            if record.review_history:
                last_review = record.review_history[-1]["timestamp"]
                if last_review >= cutoff_date:
                    recent_reviews.append(record)

        if not recent_reviews:
            return {
                "total_reviews": 0,
                "avg_rating": 0.0,
                "success_rate": 0.0,
                "avg_stability": 0.0,
                "difficulty_distribution": {}
            }

        # 计算统计数据
        total_reviews = len(recent_reviews)

        # 平均评分
        ratings = [
            review.review_history[-1]["rating"]
            for review in recent_reviews
            if review.review_history
        ]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

        # 成功率（评分>=3视为成功）
        success_count = sum(1 for rating in ratings if rating >= 3)
        success_rate = success_count / len(ratings) if ratings else 0.0

        # 平均稳定性
        avg_stability = sum(r.stability for r in recent_reviews) / total_reviews

        # 难度分布
        difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
        for review in recent_reviews:
            if review.difficulty <= 3:
                difficulty_distribution["easy"] += 1
            elif review.difficulty <= 6:
                difficulty_distribution["medium"] += 1
            else:
                difficulty_distribution["hard"] += 1

        return {
            "total_reviews": total_reviews,
            "avg_rating": avg_rating,
            "success_rate": success_rate,
            "avg_stability": avg_stability,
            "difficulty_distribution": difficulty_distribution
        }