import unittest
import os
import sys
from pathlib import Path
import shutil
from dotenv import load_dotenv

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from leetcode_fsrs_cli.auth import AuthManager
from leetcode_fsrs_cli.sync import SyncManager
from leetcode_fsrs_cli.leetcode_api import LeetCodeAPIClient

class TestRealSync(unittest.TestCase):
    def setUp(self):
        # Setup temporary data directory
        self.test_dir = Path("test_sync_data_dir")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        
        # Initialize managers with test dir
        self.auth_manager = AuthManager(data_dir=str(self.test_dir))
        self.sync_manager = SyncManager(data_dir=str(self.test_dir))
        
        # Load Cookie from .env
        load_dotenv()
        self.real_cookie = os.getenv('LEETCODE_COOKIE')
        if not self.real_cookie:
            raise unittest.SkipTest("LEETCODE_COOKIE not found in .env")
            
        # Save cookie to AuthManager so client_from_saved_cookie works
        self.auth_manager.save_cookie(self.real_cookie)

    def tearDown(self):
        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_sync_flow(self):
        print("\n🔄 Testing sync flow with real cookie...")
        
        # Perform Sync
        # We need to patch client_from_saved_cookie to use our test auth manager
        # OR we can just rely on the fact that we initialized AuthManager with the same dir
        # BUT client_from_saved_cookie instantiates AuthManager() without args, 
        # which defaults to ~/.config/leetcode-fsrs-cli.
        # So we need to patch it.
        
        from unittest.mock import patch
        
        with patch('leetcode_fsrs_cli.leetcode_api.client_from_saved_cookie') as mock_client_factory:
            # Create a client that uses our test cookie
            client = LeetCodeAPIClient(cookie=self.real_cookie)
            mock_client_factory.return_value = client
            
            report = self.sync_manager.perform_sync(full_sync=True)
            
            print(f"Sync Status: {report.status}")
            print(f"New Questions: {report.new_count}")
            print(f"Updated Questions: {report.updated_count}")
            print(f"Total Questions: {report.total_count}")
            
            self.assertEqual(report.status, "success")
            self.assertGreater(report.total_count, 0)
            
            # Verify questions are saved
            from leetcode_fsrs_cli.leetcode import QuestionManager
            qm = QuestionManager(data_dir=str(self.test_dir))
            self.assertEqual(len(qm.questions), report.total_count)
            
            first_q = list(qm.questions.values())[0]
            print(f"First synced question: {first_q.title} ({first_q.difficulty})")
            self.assertTrue(first_q.title)
            self.assertTrue(first_q.difficulty)

if __name__ == '__main__':
    unittest.main()
