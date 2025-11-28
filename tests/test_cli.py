import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from leetcode_fsrs_cli.cli import cli, LeetCodeFSRSCLI
from leetcode_fsrs_cli.leetcode import Question
from leetcode_fsrs_cli.fsrs import ReviewRecord
from datetime import datetime

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('leetcode_fsrs_cli.cli.LeetCodeFSRSCLI')
    def test_list_command(self, MockCLI):
        # Setup mock
        mock_instance = MockCLI.return_value
        
        # Run command
        result = self.runner.invoke(cli, ['list'])
        
        # Verify
        self.assertEqual(result.exit_code, 0)
        mock_instance.list_questions.assert_called_once()

    @patch('leetcode_fsrs_cli.cli.LeetCodeFSRSCLI')
    def test_practice_command(self, MockCLI):
        mock_instance = MockCLI.return_value
        
        result = self.runner.invoke(cli, ['practice', '--limit', '10'])
        
        self.assertEqual(result.exit_code, 0)
        mock_instance.practice.assert_called_with(10, show_plan=False)

    @patch('leetcode_fsrs_cli.cli.LeetCodeFSRSCLI')
    def test_practice_plan_command(self, MockCLI):
        mock_instance = MockCLI.return_value
        
        result = self.runner.invoke(cli, ['practice', '--plan'])
        
        self.assertEqual(result.exit_code, 0)
        mock_instance.practice.assert_called_with(20, show_plan=True)

    @patch('leetcode_fsrs_cli.storage.StorageManager')
    def test_config_set(self, MockStorage):
        mock_storage = MockStorage.return_value
        mock_storage.load_config.return_value = {"key": "old_value"}
        
        result = self.runner.invoke(cli, ['config', 'set', 'key', 'new_value'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("已更新", result.output)
        mock_storage.save_config.assert_called()

    @patch('leetcode_fsrs_cli.storage.StorageManager')
    def test_config_set_weights_invalid(self, MockStorage):
        result = self.runner.invoke(cli, ['config', 'set-weights', '1,2,3'])
        
        self.assertNotEqual(result.exit_code, 0) # Should fail or print error
        self.assertIn("错误", result.output)

if __name__ == '__main__':
    unittest.main()
