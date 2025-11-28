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

class TestRealIntegration(unittest.TestCase):
    def setUp(self):
        # Setup temporary data directory
        self.test_dir = Path("test_real_data_dir")
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

    def tearDown(self):
        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_real_connection(self):
        print("\n🔄 Testing connection with real cookie...")
        
        # 1. Test Authentication
        client = LeetCodeAPIClient(cookie=self.real_cookie)
        is_auth = client.is_authenticated()
        print(f"Authentication Status: {'✅ Success' if is_auth else '❌ Failed'}")
        
        if is_auth:
            username = client.get_current_username()
            print(f"Logged in as: {username}")
            self.assertIsNotNone(username)
            
            # 2. Test Fetching Problems
            print("Fetching recent problems...")
            problems = client.get_user_problems(limit=5)
            print(f"Found {len(problems)} recent problems")
            
            if problems:
                print("First problem found:", problems[0]['title'])
                
                # 3. Test Fetching Detail
                print(f"Fetching detail for: {problems[0]['slug']}")
                detail = client.get_question_detail(problems[0]['slug'])
                if detail:
                    print(f"✅ Successfully fetched detail for ID: {detail.get('id')}")
                    print(f"Title: {detail.get('title')}")
                    print(f"Difficulty: {detail.get('difficulty')}")
                else:
                    print("❌ Failed to fetch detail")
            else:
                print("⚠️ No recent problems found (this might be normal if user hasn't submitted recently)")
        
        self.assertTrue(is_auth, "Authentication failed with provided cookie")

if __name__ == '__main__':
    unittest.main()
