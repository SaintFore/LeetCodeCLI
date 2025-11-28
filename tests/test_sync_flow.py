import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import shutil
from pathlib import Path

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from leetcode_fsrs_cli.sync import SyncManager
from leetcode_fsrs_cli.leetcode import QuestionManager
from leetcode_fsrs_cli.auth import AuthManager
import leetcode_fsrs_cli.leetcode_api  # Ensure module is loaded for patch

class TestSyncFlow(unittest.TestCase):
    def setUp(self):
        # Setup temporary data directory
        self.test_dir = Path("test_data_dir")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        
        # Initialize managers with test dir
        self.auth_manager = AuthManager(data_dir=str(self.test_dir))
        self.sync_manager = SyncManager(data_dir=str(self.test_dir))
        self.question_manager = QuestionManager(data_dir=str(self.test_dir))

    def tearDown(self):
        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('leetcode_fsrs_cli.leetcode_api.requests.Session')
    @patch('leetcode_fsrs_cli.auth.AuthManager.load_cookie')
    def test_sync_process(self, mock_load_cookie, mock_session_cls):
        # 1. Mock Auth
        mock_load_cookie.return_value = "LEETCODE_SESSION=fake_cookie"
        
        # 2. Mock API Responses
        mock_session = mock_session_cls.return_value
        
        # Mock responses for different queries
        def side_effect(*args, **kwargs):
            json_data = kwargs.get('json', {})
            query = json_data.get('query', '')
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            
            if "currentUser" in query:
                # Auth check
                mock_response.json.return_value = {
                    "data": {"currentUser": {"username": "test_user"}}
                }
            elif "recentAcSubmissionList" in query:
                # Get problems list
                mock_response.json.return_value = {
                    "data": {
                        "recentAcSubmissionList": [
                            {
                                "title": "Two Sum",
                                "titleSlug": "two-sum",
                                "timestamp": "1600000000"
                            },
                            {
                                "title": "Add Two Numbers",
                                "titleSlug": "add-two-numbers",
                                "timestamp": "1600000000"
                            }
                        ]
                    }
                }
            elif "questionData" in query:
                # Get question detail
                variables = json_data.get('variables', {})
                slug = variables.get('titleSlug')
                
                if slug == "two-sum":
                    mock_response.json.return_value = {
                        "data": {
                            "question": {
                                "questionId": "1",
                                "title": "Two Sum",
                                "titleSlug": "two-sum",
                                "content": "Content for Two Sum",
                                "translatedContent": None,
                                "codeSnippets": [],
                                "difficulty": "Easy",
                                "topicTags": [{"name": "Array"}, {"name": "Hash Table"}]
                            }
                        }
                    }
                elif slug == "add-two-numbers":
                    mock_response.json.return_value = {
                        "data": {
                            "question": {
                                "questionId": "2",
                                "title": "Add Two Numbers",
                                "titleSlug": "add-two-numbers",
                                "content": "Content for Add Two Numbers",
                                "translatedContent": None,
                                "codeSnippets": [],
                                "difficulty": "Medium",
                                "topicTags": [{"name": "Linked List"}]
                            }
                        }
                    }
            
            return mock_response

        mock_session.post.side_effect = side_effect

        # 3. Run Sync
        # We need to patch client_from_saved_cookie to use our mocked auth
        with patch('leetcode_fsrs_cli.leetcode_api.client_from_saved_cookie') as mock_client_factory:
            from leetcode_fsrs_cli.leetcode_api import LeetCodeAPIClient
            # Create a client that uses our mocked session
            client = LeetCodeAPIClient(cookie="fake")
            client.session = mock_session
            mock_client_factory.return_value = client
            
            # Perform sync
            report = self.sync_manager.perform_sync()
            
            # 4. Verify Results
            self.assertEqual(report.status, "success")
            self.assertEqual(report.new_count, 2)
            
            # Verify questions are saved
            self.question_manager._load_questions() # Reload from disk
            questions = self.question_manager.list_questions()
            self.assertEqual(len(questions), 2)
            
            q1 = self.question_manager.get_question(1)
            self.assertIsNotNone(q1)
            self.assertEqual(q1.title, "Two Sum")
            self.assertEqual(q1.difficulty, "Easy")
            
            q2 = self.question_manager.get_question(2)
            self.assertIsNotNone(q2)
            self.assertEqual(q2.title, "Add Two Numbers")

if __name__ == '__main__':
    unittest.main()
