import sys
from unittest.mock import MagicMock
sys.modules["click"] = MagicMock()

import unittest
from datetime import datetime, timedelta
from leetcode_fsrs_cli.fsrs import FSRS, ReviewRecord

class TestFSRS(unittest.TestCase):
    def setUp(self):
        self.fsrs = FSRS()

    def test_initial_state(self):
        stability, difficulty = self.fsrs.get_initial_state()
        self.assertEqual(stability, 2.5)
        self.assertEqual(difficulty, 5.0)

    def test_next_interval_rating_1_forget(self):
        # Test rating 1 (Forget)
        # Should reset interval to 1 and decrease stability significantly
        stability = 5.0
        difficulty = 5.0
        rating = 1
        elapsed_days = 10.0
        
        new_s, new_d, new_i = self.fsrs.next_interval(stability, difficulty, rating, elapsed_days)
        
        self.assertEqual(new_i, 1.0)
        self.assertLess(new_s, stability)
        self.assertGreater(new_d, difficulty)

    def test_next_interval_rating_3_good(self):
        # Test rating 3 (Good)
        # Should increase interval and stability
        stability = 5.0
        difficulty = 5.0
        rating = 3
        elapsed_days = 5.0 # Reviewed exactly when due (approx)
        
        new_s, new_d, new_i = self.fsrs.next_interval(stability, difficulty, rating, elapsed_days)
        
        self.assertGreater(new_i, elapsed_days)
        self.assertGreater(new_s, stability)
        # Difficulty might change slightly depending on weights, but usually stays similar for 'Good' if it matches expectation

    def test_calculate_next_review(self):
        current_time = datetime(2023, 1, 10, 12, 0, 0)
        last_review = datetime(2023, 1, 1, 12, 0, 0) # 9 days ago
        stability = 5.0
        difficulty = 5.0
        rating = 3
        
        next_review, new_s, new_d = self.fsrs.calculate_next_review(
            current_time, stability, difficulty, rating, last_review
        )
        
        self.assertIsInstance(next_review, datetime)
        self.assertGreater(next_review, current_time)

class TestReviewRecord(unittest.TestCase):
    def setUp(self):
        self.fsrs = FSRS()
        self.record = ReviewRecord(question_id=1)

    def test_add_review(self):
        now = datetime.now()
        self.record.add_review(now, 3, self.fsrs)
        
        self.assertEqual(len(self.record.review_history), 1)
        self.assertIsNotNone(self.record.next_review)
        self.assertFalse(self.record.due)
        
        # Add another review
        next_time = self.record.next_review + timedelta(days=1)
        self.record.add_review(next_time, 4, self.fsrs)
        self.assertEqual(len(self.record.review_history), 2)

    def test_serialization(self):
        now = datetime.now()
        self.record.add_review(now, 3, self.fsrs)
        
        data = self.record.to_dict()
        loaded_record = ReviewRecord.from_dict(data)
        
        self.assertEqual(loaded_record.question_id, self.record.question_id)
        self.assertEqual(loaded_record.stability, self.record.stability)
        self.assertEqual(len(loaded_record.review_history), 1)

if __name__ == '__main__':
    unittest.main()
