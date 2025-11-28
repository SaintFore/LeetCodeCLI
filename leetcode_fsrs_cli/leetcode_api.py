"""
LeetCode GraphQL API 客户端（基础实现）

提供：
- 使用保存的 Cookie 进行请求
- 验证登录状态（获取用户信息）
- 获取用户已通过/提交的题目列表（简单版本）
- 获取题目详情（标题、描述、slug 等）

注意：这是一个基础实现，后续需要完善分页、错误重试、速率限制等。
"""

from typing import Optional, Dict, Any, List
import requests
import json
import os
from pathlib import Path
import click

GRAPHQL_URL = "https://leetcode.com/graphql"
BASE_URL = "https://leetcode.com"


class LeetCodeAPIClient:
    def __init__(self, cookie: Optional[str] = None, timeout: int = 10):
        self.session = requests.Session()
        self.timeout = timeout

        if cookie:
            self._set_cookie_header(cookie)

        # 常用请求头
        self.session.headers.update({
            "User-Agent": "leetcode-fsrs-cli/1.0",
            "Referer": "https://leetcode.com",
            "Content-Type": "application/json",
            "Origin": "https://leetcode.com"
        })

    def _set_cookie_header(self, cookie: str):
        # 支持 `LEETCODE_SESSION=xxx` 或 完整 cookie 字符串
        cookie = cookie.strip()
        
        # 尝试解析 CSRF Token
        csrf_token = None
        if "csrftoken=" in cookie:
            try:
                parts = cookie.split(";")
                for part in parts:
                    if "csrftoken=" in part:
                        csrf_token = part.split("=")[1].strip()
                        break
            except Exception:
                pass
        
        self.session.headers.update({"Cookie": cookie})
        if csrf_token:
            self.session.headers.update({"X-CSRFToken": csrf_token})

    def _post_graphql(self, query: str, variables: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        payload = {"query": query, "variables": variables or {}}
        try:
            response = self.session.post(GRAPHQL_URL, json=payload, timeout=self.timeout)
            if response.status_code != 200:
                return None
            return response.json()
        except Exception:
            return None

    def is_authenticated(self) -> bool:
        """通过请求当前用户信息判断是否登录"""
        query = """
        query globalData {
            userStatus {
                isSignedIn
                username
            }
        }
        """
        try:
            resp = self._post_graphql(query)
            if not resp:
                return False
            data = resp.get("data", {}).get("userStatus", {})
            return data.get("isSignedIn", False)
        except Exception:
            return False

    def get_current_username(self) -> Optional[str]:
        """获取当前登录用户名"""
        query = """
        query globalData {
            userStatus {
                username
            }
        }
        """
        try:
            resp = self._post_graphql(query)
            if not resp:
                return None
            return resp.get("data", {}).get("userStatus", {}).get("username")
        except Exception:
            return None

    def get_user_problems(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        获取用户已提交/已通过的题目
        优先尝试获取所有已通过题目 (REST API)，如果失败则回退到最近提交 (GraphQL)
        """
        # 尝试使用 REST API 获取所有题目状态
        try:
            url = "https://leetcode.com/api/problems/all/"
            resp = self.session.get(url, timeout=self.timeout)
            
            if resp.status_code == 200:
                data = resp.json()
                problems = []
                
                for item in data.get("stat_status_pairs", []):
                    if item.get("status") == "ac":
                        stat = item.get("stat", {})
                        problems.append({
                            "title": stat.get("question__title"),
                            "slug": stat.get("question__title_slug"),
                            "id": stat.get("question_id"),
                            "timestamp": None # REST API 不返回时间戳，但这不影响同步逻辑
                        })
                
                if problems:
                    return problems
                    
        except Exception as e:
            click.echo(f"⚠️ REST API 获取失败，回退到 GraphQL: {e}")

        # 回退到 GraphQL 获取最近提交
        # 因为需要 username，我们先尝试获取当前用户
        username = self.get_current_username()
        if not username:
            return []

        query = """
        query recentAcSubmissions($username: String!, $limit: Int!) { 
            recentAcSubmissionList(username: $username, limit: $limit) { 
                title 
                titleSlug 
                timestamp 
            } 
        }
        """
        variables = {"username": username, "limit": limit}

        try:
            resp = self._post_graphql(query, variables)
            if not resp:
                return []
            
            submissions = resp.get("data", {}).get("recentAcSubmissionList", [])
            problems = []
            for item in submissions:
                problems.append({
                    "title": item.get("title"),
                    "slug": item.get("titleSlug"),
                    "timestamp": item.get("timestamp")
                })

            return problems

        except Exception as e:
            click.echo(f"❌ 获取用户题目失败: {e}")
            return []

    def get_question_detail(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        获取题目详情，使用 GraphQL 的 questionData 查询
        返回字典，包含 title, content, codeSnippets, difficulty, tags 等
        """
        query = """
        query questionData($titleSlug: String!) { 
            question(titleSlug: $titleSlug) { 
                questionId 
                title 
                titleSlug 
                content 
                translatedContent 
                codeSnippets {
                    lang
                    langSlug
                    code
                }
                difficulty 
                topicTags { 
                    name 
                    slug 
                } 
            } 
        }
        """
        variables = {"titleSlug": slug}

        try:
            resp = self._post_graphql(query, variables)
            if not resp:
                return None
            
            q = resp.get("data", {}).get("question")
            if not q:
                return None

            tags = [tag["name"] for tag in q.get("topicTags", [])]

            return {
                "id": int(q.get("questionId")) if q.get("questionId") else None,
                "title": q.get("title"),
                "slug": q.get("titleSlug"),
                "difficulty": q.get("difficulty"),
                "tags": tags,
                "content": q.get("content") or q.get("translatedContent"),
                "code_snippets": q.get("codeSnippets")
            }

        except Exception as e:
            click.echo(f"❌ 获取题目详情失败: {e}")
            return None


def client_from_saved_cookie() -> Optional[LeetCodeAPIClient]:
    """从保存的Cookie创建客户端"""
    from .auth import AuthManager
    
    auth_manager = AuthManager()
    auth_manager = AuthManager()
    cookie = auth_manager.load_cookie()
    
    if not cookie:
        return None
        
    return LeetCodeAPIClient(cookie=cookie)
