"""
CLI交互界面
提供命令行交互功能
"""

import click
import sys
from datetime import datetime
from typing import List, Optional

from .fsrs import FSRS, ReviewRecord
from .leetcode import QuestionManager, Question, SAMPLE_QUESTIONS
from .storage import StorageManager
from .scheduler import ReviewScheduler, ReviewSession


class LeetCodeFSRSCLI:
    """LeetCode FSRS CLI 主类"""

    def __init__(self):
        self.question_manager = QuestionManager()
        self.storage_manager = StorageManager()
        self.fsrs = FSRS()
        self.scheduler = ReviewScheduler(self.fsrs)

    def init_project(self):
        """初始化项目"""
        # 显示数据目录信息
        data_dir = self.question_manager.data_dir
        click.echo(f"📁 数据目录: {data_dir}")

        # 添加示例题目
        for question in SAMPLE_QUESTIONS:
            self.question_manager.add_question(question)

        # 创建默认配置
        config = self.storage_manager.load_config()
        self.storage_manager.save_config(config)

        click.echo("✅ 项目初始化完成！")
        click.echo(f"📚 已添加 {len(SAMPLE_QUESTIONS)} 个示例题目")
        click.echo(f"💾 数据保存在: {data_dir}")

    def add_question(self, question_id: int, title: str, difficulty: str, tags: List[str]):
        """添加题目"""
        url = f"https://leetcode.com/problems/{title.lower().replace(' ', '-')}/"

        question = Question(
            id=question_id,
            title=title,
            difficulty=difficulty,
            tags=tags,
            url=url
        )

        if self.question_manager.add_question(question):
            click.echo(f"✅ 题目 {question_id}. {title} 添加成功！")
        else:
            click.echo(f"❌ 题目 {question_id} 已存在！")

    def practice(self, limit: int = 20):
        """开始练习"""
        # 获取到期的复习记录
        due_reviews = self.storage_manager.get_due_reviews()

        if not due_reviews:
            click.echo("🎉 没有到期的复习题目！")
            return

        # 生成复习计划
        questions = {q.id: q for q in self.question_manager.list_questions()}
        sessions = self.scheduler.generate_daily_review_plan(
            due_reviews, questions, limit
        )

        if not sessions:
            click.echo("❌ 没有可复习的题目！")
            return

        click.echo(f"📚 今日复习计划 ({len(sessions)} 题):")
        click.echo("=" * 50)

        completed_count = 0
        for i, session in enumerate(sessions, 1):
            question = session.question
            review = session.review_record

            click.echo(f"\n{i}. {question.id}. {question.title}")
            click.echo(f"   难度: {question.difficulty}")
            click.echo(f"   标签: {', '.join(question.tags)}")
            click.echo(f"   稳定性: {review.stability:.2f}")
            click.echo(f"   难度系数: {review.difficulty:.2f}")

            # 获取用户评分
            rating = self._get_user_rating()
            if rating is None:
                click.echo("\n👋 练习结束！")
                break

            # 更新复习记录
            review.add_review(datetime.now(), rating, self.fsrs)
            self.storage_manager.save_review_record(review)

            completed_count += 1

            # 显示进度
            progress = self.scheduler.calculate_review_progress(
                sessions, completed_count
            )
            click.echo(f"\n📊 进度: {completed_count}/{len(sessions)} "
                      f"({progress['completion_rate']:.1%})")

        click.echo(f"\n🎯 今日完成: {completed_count} 题")

    def _get_user_rating(self) -> Optional[int]:
        """获取用户评分"""
        click.echo("\n请评价回忆难度:")
        click.echo("1. 完全忘记")
        click.echo("2. 很困难")
        click.echo("3. 中等难度")
        click.echo("4. 简单")
        click.echo("5. 完美掌握")
        click.echo("0. 退出练习")

        while True:
            try:
                choice = click.prompt("请输入选择 (1-5, 0退出)", type=int)
                if 0 <= choice <= 5:
                    return choice if choice != 0 else None
                else:
                    click.echo("❌ 请输入 0-5 之间的数字")
            except ValueError:
                click.echo("❌ 请输入有效的数字")

    def stats(self):
        """显示统计信息"""
        # 题目统计
        question_counts = self.question_manager.get_question_count_by_difficulty()
        total_questions = sum(question_counts.values())

        # 复习统计
        review_stats = self.storage_manager.get_review_stats()

        click.echo("📊 学习统计")
        click.echo("=" * 30)

        click.echo(f"\n📚 题目统计:")
        click.echo(f"   总题目数: {total_questions}")
        click.echo(f"   Easy: {question_counts['easy']}")
        click.echo(f"   Medium: {question_counts['medium']}")
        click.echo(f"   Hard: {question_counts['hard']}")

        click.echo(f"\n📖 复习统计:")
        click.echo(f"   总复习数: {review_stats['total_reviews']}")
        click.echo(f"   待复习: {review_stats['due_reviews']}")
        click.echo(f"   平均稳定性: {review_stats['avg_stability']:.2f}")

        # 学习分析
        all_reviews = list(self.storage_manager.load_reviews().values())
        analytics = self.scheduler.get_study_analytics(all_reviews)

        click.echo(f"\n📈 近期学习分析 (30天):")
        click.echo(f"   复习次数: {analytics['total_reviews']}")
        click.echo(f"   平均评分: {analytics['avg_rating']:.2f}")
        click.echo(f"   成功率: {analytics['success_rate']:.1%}")

    def schedule(self):
        """生成复习计划"""
        due_reviews = self.storage_manager.get_due_reviews()
        questions = {q.id: q for q in self.question_manager.list_questions()}

        if not due_reviews:
            click.echo("🎉 没有到期的复习题目！")
            return

        sessions = self.scheduler.generate_daily_review_plan(
            due_reviews, questions, 20
        )

        click.echo("📅 复习计划")
        click.echo("=" * 40)
        click.echo(f"待复习题目: {len(sessions)}")
        click.echo()

        for i, session in enumerate(sessions[:10], 1):  # 只显示前10个
            question = session.question
            click.echo(f"{i}. {question.id}. {question.title}")
            click.echo(f"   难度: {question.difficulty}")
            click.echo(f"   优先级: {session.priority:.2f}")
            click.echo()

        if len(sessions) > 10:
            click.echo(f"... 还有 {len(sessions) - 10} 题")

    def list_questions(self, difficulty: Optional[str] = None, tag: Optional[str] = None):
        """列出题目"""
        tags = [tag] if tag else None
        questions = self.question_manager.list_questions(difficulty, tags)

        if not questions:
            click.echo("❌ 没有找到符合条件的题目")
            return

        click.echo(f"📚 题目列表 ({len(questions)} 题)")
        click.echo("=" * 50)

        for question in questions:
            review = self.storage_manager.get_review_record(question.id)
            status = "✅ 已复习" if review else "🆕 未开始"

            click.echo(f"{question.id}. {question.title}")
            click.echo(f"   难度: {question.difficulty}")
            click.echo(f"   标签: {', '.join(question.tags)}")
            click.echo(f"   状态: {status}")
            if review and review.next_review:
                click.echo(f"   下次复习: {review.next_review.strftime('%Y-%m-%d')}")
            click.echo()

    def search_questions(self, keyword: str):
        """搜索题目"""
        questions = self.question_manager.search_questions(keyword)

        if not questions:
            click.echo(f"❌ 没有找到包含 '{keyword}' 的题目")
            return

        click.echo(f"🔍 搜索结果 ({len(questions)} 题)")
        click.echo("=" * 40)

        for question in questions:
            click.echo(f"{question.id}. {question.title}")
            click.echo(f"   难度: {question.difficulty}")
            click.echo(f"   标签: {', '.join(question.tags)}")
            click.echo()


# CLI命令定义

@click.group()
@click.pass_context
def cli(ctx):
    """LeetCode FSRS CLI - 基于FSRS算法的LeetCode刷题工具"""
    ctx.obj = LeetCodeFSRSCLI()


@cli.command()
def init():
    """初始化项目"""
    cli = LeetCodeFSRSCLI()
    cli.init_project()


@cli.command()
@click.argument('question_id', type=int)
@click.argument('title')
@click.argument('difficulty')
@click.argument('tags')
def add(question_id, title, difficulty, tags):
    """添加题目"""
    cli = LeetCodeFSRSCLI()
    tag_list = [tag.strip() for tag in tags.split(',')]
    cli.add_question(question_id, title, difficulty, tag_list)


@cli.command()
@click.option('--limit', default=20, help='每日复习题目数量限制')
def practice(limit):
    """开始练习"""
    cli = LeetCodeFSRSCLI()
    cli.practice(limit)


@cli.command()
def stats():
    """显示统计信息"""
    cli = LeetCodeFSRSCLI()
    cli.stats()


@cli.command()
def schedule():
    """生成复习计划"""
    cli = LeetCodeFSRSCLI()
    cli.schedule()


@cli.command()
@click.option('--difficulty', help='按难度过滤')
@click.option('--tag', help='按标签过滤')
def list(difficulty, tag):
    """列出题目"""
    cli = LeetCodeFSRSCLI()
    cli.list_questions(difficulty, tag)


@cli.command()
@click.argument('keyword')
def search(keyword):
    """搜索题目"""
    cli = LeetCodeFSRSCLI()
    cli.search_questions(keyword)


if __name__ == '__main__':
    cli()