"""
数据同步模块
负责将LeetCode账户的题目与本地数据库同步
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import json
import os
from pathlib import Path
import click


@dataclass
class SyncReport:
    """同步报告"""
    timestamp: str
    new_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    total_count: int = 0
    status: str = "pending"  # pending, success, failed


class SyncManager:
    """同步管理器 - 管理LeetCode与本地的数据同步"""

    def __init__(self, data_dir: str = None):
        # 使用 XDG 标准目录
        if data_dir is None:
            xdg_config_home = os.environ.get('XDG_CONFIG_HOME',
                                            os.path.expanduser('~/.config'))
            self.data_dir = Path(xdg_config_home) / "leetcode-fsrs-cli"
        else:
            self.data_dir = Path(data_dir)

        self.sync_state_file = self.data_dir / "sync_state.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_sync_state(self) -> dict:
        """
        获取同步状态

        Returns:
            dict: 同步状态信息
        """
        if not os.path.exists(self.sync_state_file):
            return {
                "last_sync": None,
                "total_synced": 0,
                "user_id": None,
                "sync_history": []
            }

        try:
            with open(self.sync_state_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            click.echo(f"❌ 读取同步状态失败: {e}")
            return {
                "last_sync": None,
                "total_synced": 0,
                "user_id": None,
                "sync_history": []
            }

    def save_sync_state(self, state: dict) -> bool:
        """
        保存同步状态

        Args:
            state: 同步状态字典

        Returns:
            bool: 是否成功保存
        """
        try:
            with open(self.sync_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            return True

        except Exception as e:
            click.echo(f"❌ 保存同步状态失败: {e}")
            return False

    def add_sync_record(self, report: SyncReport) -> bool:
        """
        添加同步记录

        Args:
            report: 同步报告

        Returns:
            bool: 是否成功添加
        """
        try:
            state = self.get_sync_state()

            # 添加到历史记录
            sync_record = {
                "timestamp": report.timestamp,
                "new_count": report.new_count,
                "updated_count": report.updated_count,
                "unchanged_count": report.unchanged_count,
                "total_count": report.total_count,
                "status": report.status
            }

            state["sync_history"].append(sync_record)

            # 保持最近100条记录
            if len(state["sync_history"]) > 100:
                state["sync_history"] = state["sync_history"][-100:]

            # 更新最后同步时间
            if report.status == "success":
                state["last_sync"] = report.timestamp
                state["total_synced"] = report.total_count

            return self.save_sync_state(state)

        except Exception as e:
            click.echo(f"❌ 添加同步记录失败: {e}")
            return False

    def get_last_sync_time(self) -> Optional[str]:
        """
        获取最后同步时间

        Returns:
            Optional[str]: 最后同步时间，如果从未同步返回None
        """
        state = self.get_sync_state()
        return state.get("last_sync")

    def perform_sync(self, full_sync: bool = False) -> SyncReport:
        """
        执行同步操作

        Args:
            full_sync: 是否执行完整同步

        Returns:
            SyncReport: 同步报告
        """
        from .leetcode_api import client_from_saved_cookie
        from .leetcode import QuestionManager, Question

        report = SyncReport(
            timestamp=datetime.now().isoformat(),
            status="failed"
        )

        # 1. 获取API客户端
        client = client_from_saved_cookie()
        if not client or not client.is_authenticated():
            click.echo("❌ 未认证或Cookie已失效")
            return report

        # 2. 获取本地题目
        qm = QuestionManager(data_dir=str(self.data_dir))
        local_questions = qm.questions
        report.total_count = len(local_questions)

        # 3. 获取远程题目列表
        click.echo("🔄 正在获取远程题目列表...")
        # TODO: 支持分页获取所有题目，目前仅获取最近50个
        remote_problems = client.get_user_problems(limit=50)
        if not remote_problems:
            click.echo("⚠️ 未获取到远程题目或列表为空")
            report.status = "success"  # 视为空列表为成功
            return report

        # 4. 对比和同步
        click.echo(f"🔍 发现 {len(remote_problems)} 个最近提交，正在分析差异...")
        
        with click.progressbar(remote_problems, label="同步进度") as bar:
            for prob in bar:
                # 这里的 prob 只有 title, slug, timestamp
                # 我们需要获取详情来得到 id
                # 但为了避免过多请求，我们先用 slug 检查是否可能已存在（如果本地存了 slug）
                # 目前本地 Question 模型没有 slug 字段，只有 url
                # url 格式: https://leetcode.com/problems/{slug}/
                
                slug = prob.get("slug")
                if not slug:
                    continue
                    
                # 检查本地是否已存在该题目 (通过 URL 匹配)
                # 这是一个简单的检查，不够严谨，但能减少请求
                exists = False
                for q in local_questions.values():
                    if slug in q.url:
                        exists = True
                        break
                
                if exists and not full_sync:
                    report.unchanged_count += 1
                    continue

                # 获取详细信息
                detail = client.get_question_detail(slug)
                if not detail:
                    continue

                qid = detail.get("id")
                if not qid:
                    continue

                # 再次检查 ID 是否存在
                if qid in local_questions and not full_sync:
                    report.unchanged_count += 1
                    continue

                # 创建或更新题目
                question = Question(
                    id=qid,
                    title=detail.get("title"),
                    difficulty=detail.get("difficulty") or "Unknown",
                    tags=detail.get("tags") or [],
                    url=f"https://leetcode.com/problems/{slug}/",
                    content=detail.get("content") or ""
                )
                
                if qid in local_questions:
                    # 更新
                    qm.add_question(question) # add_question 会覆盖
                    report.updated_count += 1
                else:
                    # 新增
                    qm.add_question(question)
                    report.new_count += 1

        report.total_count = len(qm.questions)
        report.status = "success"
        
        # 保存同步记录
        self.add_sync_record(report)
        
        return report

    def compare_remote_and_local(self, remote_questions: List[dict], 
                                 local_questions: Dict[int, dict]) -> tuple:
        """
        对比远程和本地题目

        Args:
            remote_questions: 远程获取的题目列表
            local_questions: 本地题目字典

        Returns:
            tuple: (新题目列表, 更新题目列表, 未变化数量)
        """
        new_questions = []
        updated_questions = []
        unchanged_count = 0

        for remote_q in remote_questions:
            qid = remote_q.get("id")
            if qid not in local_questions:
                new_questions.append(remote_q)
            else:
                # TODO: 实现详细的更新检查逻辑
                # 这里可以比较提交状态、通过率等字段
                unchanged_count += 1

        return new_questions, updated_questions, unchanged_count

    def display_sync_summary(self, new_count: int, updated_count: int, 
                            unchanged_count: int, total_count: int) -> None:
        """
        显示同步摘要

        Args:
            new_count: 新题目数量
            updated_count: 更新题目数量
            unchanged_count: 未变化题目数量
            total_count: 总题目数量
        """
        click.echo("\n" + "=" * 50)
        click.echo("📊 同步摘要:")
        click.echo(f"   新增题目: {new_count}")
        click.echo(f"   更新题目: {updated_count}")
        click.echo(f"   未变化: {unchanged_count}")
        click.echo(f"   总计: {total_count}")
        click.echo("=" * 50)
