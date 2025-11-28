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
from .auth import AuthManager
from .sync import SyncManager, SyncReport


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

        # 创建默认配置
        config = self.storage_manager.load_config()
        self.storage_manager.save_config(config)

        click.echo("\n✅ 项目初始化完成！")
        click.echo("\n📝 后续步骤:")
        click.echo("   1. 认证: leetcode-fsrs auth login")
        click.echo("   2. 同步: leetcode-fsrs sync")
        click.echo("   3. 练习: leetcode-fsrs practice")
        click.echo(f"\n💾 数据保存在: {data_dir}")

    def practice(self, limit: int = 20):
        """开始练习"""
        # 获取到期的复习记录
        due_reviews = self.storage_manager.get_due_reviews()
        questions = {q.id: q for q in self.question_manager.list_questions()}
        
        # 如果复习题目不足，补充新题目
        new_reviews = []
        if len(due_reviews) < limit:
            needed = limit - len(due_reviews)
            # 查找没有复习记录的题目
            existing_review_ids = set(self.storage_manager.load_reviews().keys())
            new_questions = [
                q for q_id, q in questions.items() 
                if q_id not in existing_review_ids
            ]
            # 简单按ID排序取前N个
            new_questions.sort(key=lambda q: q.id, reverse=True)
            
            for q in new_questions[:needed]:
                # 创建初始复习记录
                new_reviews.append(ReviewRecord(question_id=q.id))
        
        # 合并复习列表
        all_reviews = due_reviews + new_reviews

        if not all_reviews:
            click.echo("🎉 没有需要复习或新的题目！")
            return

        # 生成复习计划
        sessions = self.scheduler.generate_daily_review_plan(
            all_reviews, questions, limit
        )

        if not sessions:
            click.echo("❌ 没有可复习的题目！")
            return

        click.echo(f"📚 今日复习计划 ({len(sessions)} 题):")
        if new_reviews:
            click.echo(f"   (包含 {len(new_reviews)} 个新题目)")
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

    def list_questions(self, difficulty: Optional[str] = None, tag: Optional[str] = None, status: Optional[str] = None):
        """列出题目"""
        tags = [tag] if tag else None
        questions = self.question_manager.list_questions(difficulty, tags)

        # 按状态过滤
        if status:
            filtered_questions = []
            for question in questions:
                review = self.storage_manager.get_review_record(question.id)
                if status == "due" and review and review.next_review and review.next_review <= datetime.now().date():
                    filtered_questions.append(question)
                elif status == "done" and review and review.next_review and review.next_review > datetime.now().date():
                    filtered_questions.append(question)
                elif status == "new" and not review:
                    filtered_questions.append(question)
            questions = filtered_questions

        if not questions:
            click.echo("❌ 没有找到符合条件的题目")
            return

        click.echo(f"📚 题目列表 ({len(questions)} 题)")
        click.echo("=" * 60)

        for question in questions:
            review = self.storage_manager.get_review_record(question.id)
            if not review:
                status_str = "🆕 未开始"
                next_review_str = ""
            elif review.next_review and review.next_review <= datetime.now().date():
                status_str = "⏰ 待复习"
                next_review_str = f"   下次复习: {review.next_review.strftime('%Y-%m-%d')}"
            else:
                status_str = "✅ 已复习"
                next_review_str = f"   下次复习: {review.next_review.strftime('%Y-%m-%d') if review.next_review else 'N/A'}"

            click.echo(f"{question.id}. {question.title}")
            click.echo(f"   难度: {question.difficulty}")
            click.echo(f"   标签: {', '.join(question.tags)}")
            click.echo(f"   状态: {status_str}")
            if next_review_str:
                click.echo(next_review_str)
            click.echo()

    def get_question_info(self, question_id: int):
        """显示题目详细信息"""
        question = self.question_manager.get_question(question_id)
        
        if not question:
            click.echo(f"❌ 题目 {question_id} 不存在")
            return
        
        review = self.storage_manager.get_review_record(question_id)
        
        click.echo("=" * 60)
        click.echo(f"📌 题目 {question.id}: {question.title}")
        click.echo("=" * 60)
        
        click.echo(f"\n📊 基本信息:")
        click.echo(f"   难度: {question.difficulty}")
        click.echo(f"   标签: {', '.join(question.tags)}")
        click.echo(f"   链接: {question.url}")
        
        if review:
            click.echo(f"\n📈 复习信息:")
            click.echo(f"   稳定性: {review.stability:.2f}")
            click.echo(f"   难度系数: {review.difficulty:.2f}")
            click.echo(f"   复习次数: {len(review.review_log) if hasattr(review, 'review_log') else 0}")
            if review.next_review:
                click.echo(f"   下次复习: {review.next_review.strftime('%Y-%m-%d')}")
        else:
            click.echo(f"\n📝 状态: 未开始复习")
        
        if question.content:
            click.echo(f"\n📖 题目描述:")
            click.echo(f"   {question.content[:200]}...")
        
        click.echo("\n" + "=" * 60)

@click.group()
@click.pass_context
def cli(ctx):
    """LeetCode FSRS CLI - 基于FSRS算法的LeetCode刷题工具"""
    ctx.obj = LeetCodeFSRSCLI()


@cli.command()
def init():
    """初始化项目"""
    cli_obj = LeetCodeFSRSCLI()
    cli_obj.init_project()


@cli.command()
@click.option('--limit', default=20, help='每日复习题目数量限制')
def practice(limit):
    """开始练习"""
    cli_obj = LeetCodeFSRSCLI()
    cli_obj.practice(limit)


@cli.command()
def stats():
    """显示统计信息"""
    cli_obj = LeetCodeFSRSCLI()
    cli_obj.stats()


@cli.command()
def schedule():
    """生成复习计划"""
    cli_obj = LeetCodeFSRSCLI()
    cli_obj.schedule()


@cli.command()
@click.option('--difficulty', help='按难度过滤 (easy/medium/hard)')
@click.option('--tag', help='按标签过滤')
@click.option('--status', help='按状态过滤 (due/done/new)')
def list(difficulty, tag, status):
    """列出题目"""
    cli_obj = LeetCodeFSRSCLI()
    cli_obj.list_questions(difficulty, tag, status)


@cli.command()
@click.argument('question_id', type=int)
def info(question_id):
    """显示题目详细信息"""
    cli_obj = LeetCodeFSRSCLI()
    cli_obj.get_question_info(question_id)


# ==================== 认证命令组 ====================

@cli.group()
def auth():
    """认证管理"""
    pass


@auth.command()
def login():
    """登录 LeetCode"""
    auth_manager = AuthManager()
    
    click.echo("\n" + "=" * 50)
    click.echo("🔐 LeetCode Cookie 登录")
    click.echo("=" * 50)
    click.echo("\n获取Cookie的步骤:")
    click.echo("1. 访问 https://leetcode.com")
    click.echo("2. 登录您的LeetCode账户")
    click.echo("3. 打开浏览器开发者工具 (F12)")
    click.echo("4. 进入 应用 > Cookie > 查找 LEETCODE_SESSION")
    click.echo("5. 复制其值或导出所有Cookie")
    click.echo("\n可接受的格式:")
    click.echo("- LEETCODE_SESSION=xxx")
    click.echo("- 完整Cookie字符串")
    
    cookie = click.prompt("\n请粘贴Cookie内容", hide_input=True)
    
    if not cookie or len(cookie.strip()) < 10:
        click.echo("❌ Cookie太短或为空，请重试")
        return
    
    if auth_manager.verify_cookie(cookie):
        if auth_manager.save_cookie(cookie.strip()):
            click.echo("✅ Cookie已保存成功！")
            click.echo("📝 下一步: 运行 'leetcode-fsrs sync' 同步您的题目")
        else:
            click.echo("❌ 保存Cookie失败")
    else:
        click.echo("⚠️ Cookie格式可能不正确，但已尝试保存")
        if auth_manager.save_cookie(cookie.strip()):
            click.echo("✅ Cookie已保存，但需要验证")
        else:
            click.echo("❌ 保存Cookie失败")


@auth.command()
def logout():
    """登出并清除认证信息"""
    auth_manager = AuthManager()
    
    if click.confirm("确定要清除保存的Cookie吗?"):
        if auth_manager.clear_auth():
            click.echo("✅ 已清除认证信息")
        else:
            click.echo("❌ 清除失败")
    else:
        click.echo("已取消")


@auth.command()
def status():
    """查看认证状态"""
    auth_manager = AuthManager()
    auth_info = auth_manager.get_auth_info()
    
    click.echo("\n" + "=" * 50)
    click.echo("🔐 认证状态")
    click.echo("=" * 50)
    
    if auth_info.get("authenticated"):
        click.echo(f"✅ 已认证")
        click.echo(f"   用户ID: {auth_info.get('user_id')}")
        click.echo(f"   Cookie: {auth_info.get('cookie')}")
    else:
        click.echo("❌ 未认证")
        click.echo("📝 运行 'leetcode-fsrs auth login' 来认证")
    
    click.echo("=" * 50)


# ==================== 同步命令 ====================

@cli.command()
@click.option('--full', is_flag=True, help='执行完整重新同步')
def sync(full):
    """同步LeetCode题目"""
    auth_manager = AuthManager()
    sync_manager = SyncManager()
    
    # 检查认证状态
    auth_info = auth_manager.get_auth_info()
    if not auth_info.get("authenticated"):
        click.echo("❌ 未认证，请先运行 'leetcode-fsrs auth login'")
        return
    
    click.echo("\n🔄 正在从LeetCode同步题目...")
    
    report = sync_manager.perform_sync(full_sync=full)
    
    if report.status == "success":
        sync_manager.display_sync_summary(
            report.new_count, 
            report.updated_count, 
            report.unchanged_count, 
            report.total_count
        )
        click.echo("✅ 同步完成！")
    else:
        click.echo("❌ 同步失败，请检查网络或Cookie是否过期")


if __name__ == '__main__':
    cli()