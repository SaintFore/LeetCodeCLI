import sys
from unittest.mock import MagicMock
sys.modules["click"] = MagicMock()

import unittest
from datetime import datetime, timedelta
from leetcode_fsrs_cli.scheduler import ReviewScheduler, ReviewSession
from leetcode_fsrs_cli.fsrs import FSRS, ReviewRecord
from leetcode_fsrs_cli.leetcode import Question

class TestReviewScheduler(unittest.TestCase):
    def setUp(self):
        self.fsrs = FSRS()
        self.scheduler = ReviewScheduler(self.fsrs)

    def test_calculate_priority(self):
        # Setup dummy question
        question = Question(1, "Q1", "Easy", [], "url")
        
        # Due review
        record = ReviewRecord(1)
        record.next_review = datetime.now() - timedelta(days=1) # Overdue
        priority = self.scheduler._calculate_priority(record, question)
        self.assertGreater(priority, 0) # Should be high priority

        # Not due review
        record.next_review = datetime.now() + timedelta(days=5)
        priority_not_due = self.scheduler._calculate_priority(record, question)
        self.assertGreater(priority_not_due, 0) # Should have some priority based on difficulty/stability
        self.assertLess(priority_not_due, priority) # But less than overdue

        # New card (no next_review)
        record.next_review = None
        priority = self.scheduler._calculate_priority(record, question)
        self.assertGreater(priority, 0) # Should have some priority

    def test_generate_daily_review_plan(self):
        # Setup questions
        questions = {
            1: Question(1, "Q1", "Easy", [], "url"),
            2: Question(2, "Q2", "Medium", [], "url"),
            3: Question(3, "Q3", "Hard", [], "url")
        }
        
        # Setup reviews
        # Q1: Overdue
        r1 = ReviewRecord(1)
        r1.next_review = datetime.now() - timedelta(days=2)
        
        # Q2: Due today
        r2 = ReviewRecord(2)
        r2.next_review = datetime.now()
        
        # Q3: New (no review record passed in due_reviews list usually, but let's simulate)
        r3 = ReviewRecord(3)
        
        due_reviews = [r1, r2, r3]
        
        sessions = self.scheduler.generate_daily_review_plan(due_reviews, questions, limit=2)
        
        self.assertEqual(len(sessions), 2)
        # Should prioritize overdue (r1) and due (r2)
        self.assertEqual(sessions[0].question.id, 1)
        self.assertEqual(sessions[1].question.id, 2)

    def test_calculate_review_progress(self):
        sessions = [ReviewSession(Question(i, f"Q{i}", "Easy", [], ""), ReviewRecord(i), 0) for i in range(10)]
        
        progress = self.scheduler.calculate_review_progress(sessions, 3)
        self.assertAlmostEqual(progress['completion_rate'], 0.3)
        self.assertEqual(progress['remaining_count'], 7)

if __name__ == '__main__':
    unittest.main()
