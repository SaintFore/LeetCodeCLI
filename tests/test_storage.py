import sys
from unittest.mock import MagicMock
sys.modules["click"] = MagicMock()

import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
from leetcode_fsrs_cli.storage import StorageManager
from leetcode_fsrs_cli.fsrs import ReviewRecord

class TestStorageManager(unittest.TestCase):
    def setUp(self):
        # Patch Path.mkdir to avoid creating directories
        self.mkdir_patcher = patch('pathlib.Path.mkdir')
        self.mock_mkdir = self.mkdir_patcher.start()
        
        # Patch os.environ to control XDG_CONFIG_HOME
        self.env_patcher = patch.dict(os.environ, {'XDG_CONFIG_HOME': '/tmp/test_config'})
        self.env_patcher.start()

    def tearDown(self):
        self.mkdir_patcher.stop()
        self.env_patcher.stop()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    def test_load_config_exists(self, mock_file, mock_exists):
        mock_exists.return_value = True
        storage = StorageManager()
        config = storage.load_config()
        
        self.assertEqual(config.get("test"), "data")
        # Should contain default values merged
        self.assertIn("fsrs_params", config)

    @patch('os.path.exists')
    def test_load_config_not_exists(self, mock_exists):
        mock_exists.return_value = False
        storage = StorageManager()
        config = storage.load_config()
        
        # Should return default config
        self.assertIn("fsrs_params", config)
        self.assertIn("daily_review_limit", config)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_config(self, mock_file):
        storage = StorageManager()
        config = {"key": "value"}
        storage.save_config(config)
        
        mock_file.assert_called_with(storage.config_file, 'w', encoding='utf-8')
        # Check if json.dump was called (write was called on file handle)
        handle = mock_file()
        handle.write.assert_called()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_reviews(self, mock_file, mock_exists):
        mock_exists.return_value = True
        # Mock review data
        review_data = {
            "1": {
                "question_id": 1,
                "review_history": [],
                "stability": 2.5,
                "difficulty": 5.0,
                "next_review": None,
                "due": False
            }
        }
        mock_file.return_value.read.return_value = json.dumps(review_data)
        
        storage = StorageManager()
        reviews = storage.load_reviews()
        
        self.assertIn(1, reviews)
        self.assertIsInstance(reviews[1], ReviewRecord)

    @patch('builtins.open', new_callable=mock_open)
    @patch('leetcode_fsrs_cli.storage.StorageManager.load_reviews')
    def test_save_review_record(self, mock_load, mock_file):
        storage = StorageManager()
        mock_load.return_value = {}
        
        record = ReviewRecord(question_id=1)
        storage.save_review_record(record)
        
        # Should load existing, update, and save back
        mock_load.assert_called_once()
        mock_file.assert_called_with(storage.reviews_file, 'w', encoding='utf-8')

if __name__ == '__main__':
    unittest.main()
