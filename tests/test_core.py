import unittest

from highlights.core import Reel


class BasicTest(unittest.TestCase):
    def test_empty_reel(self):
        self.assertEqual(Reel(500, 10, 0).clips_out(), [])

    def test_below_min_score_is_ignored(self):
        reel = Reel(500, 10, 50)
        self.assertFalse(reel.submit("e1", 10, 0))
        self.assertEqual(reel.count(), 0)

    def test_single_event_makes_one_clip(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        self.assertEqual(reel.count(), 1)

    def test_quota_is_stored(self):
        self.assertEqual(Reel(500, 7, 0).quota, 7)

    def test_scanned_starts_at_zero(self):
        self.assertEqual(Reel(500, 10, 0).scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()
