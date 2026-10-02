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


class MergeBoundaryTest(unittest.TestCase):
    def test_gap_equal_to_merge_ms_merges(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 500)
        self.assertEqual(reel.count(), 1)
        self.assertEqual(reel.clips_out(), [(0, 500, 20)])

    def test_gap_above_merge_ms_does_not_merge(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 501)
        self.assertEqual(reel.count(), 2)

    def test_merge_keeps_max_score(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 100)
        self.assertEqual(reel.clips_out()[0][2], 20)

    def test_merge_takes_union_of_ranges(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 1000)
        reel.submit("e2", 20, 400)
        reel.submit("e3", 5, 700)
        self.assertEqual(reel.clips_out(), [(400, 1000, 20)])

    def test_event_bridges_two_clips(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 30, 900)
        reel.submit("e3", 20, 450)
        self.assertEqual(reel.clips_out(), [(0, 900, 30)])


class QuotaTest(unittest.TestCase):
    def test_quota_drops_lowest_score(self):
        reel = Reel(100, 2, 0)
        reel.submit("e1", 5, 0)
        reel.submit("e2", 50, 1000)
        reel.submit("e3", 20, 2000)
        self.assertEqual(reel.count(), 2)
        self.assertEqual([c[2] for c in reel.clips_out()], [50, 20])

    def test_quota_tie_drops_later_start(self):
        reel = Reel(100, 2, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 30, 1000)
        reel.submit("e3", 10, 2000)
        self.assertEqual([c[0] for c in reel.clips_out()], [0, 1000])

    def test_quota_counts_merged_clip_once(self):
        reel = Reel(500, 1, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 100)
        self.assertEqual(reel.count(), 1)


class DedupTest(unittest.TestCase):
    def test_same_event_id_counts_once(self):
        reel = Reel(100, 10, 0)
        reel.submit("same", 10, 0)
        reel.submit("same", 10, 5000)
        self.assertEqual(reel.count(), 1)

    def test_replay_is_idempotent(self):
        events = [("e1", 10, 0), ("e2", 20, 500), ("e3", 5, 9000)]
        first = Reel(500, 10, 0)
        for event in events:
            first.submit(*event)
        second = Reel(500, 10, 0)
        for event in events + events:
            second.submit(*event)
        self.assertEqual(first.clips_out(), second.clips_out())


class OrderAndCostTest(unittest.TestCase):
    def test_output_sorted_by_start(self):
        reel = Reel(100, 10, 0)
        reel.submit("e1", 10, 3000)
        reel.submit("e2", 10, 1000)
        reel.submit("e3", 10, 2000)
        self.assertEqual([c[0] for c in reel.clips_out()], [1000, 2000, 3000])

    def test_scanned_does_not_grow_linearly(self):
        reel = Reel(1, 10000, 0)
        for index in range(3000):
            reel.submit("e-%d" % index, 10, index * 100)
        for _ in range(3000):
            reel.clips_out()
        self.assertLessEqual(reel.scanned_count(), 6000)
