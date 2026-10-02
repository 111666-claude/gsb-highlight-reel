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


class MergeTest(unittest.TestCase):
    def test_gap_equal_to_merge_ms_merges(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 500)
        self.assertEqual(reel.count(), 1)
        self.assertEqual(reel.clips_out(), [(0, 500, 20)])

    def test_gap_beyond_merge_ms_stays_apart(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 501)
        self.assertEqual(reel.count(), 2)

    def test_merge_takes_max_score(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 20, 0)
        reel.submit("e2", 10, 100)
        self.assertEqual(reel.clips_out()[0][2], 20)

    def test_merge_takes_union_of_ranges(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 1000)
        reel.submit("e2", 5, 600)
        self.assertEqual(reel.clips_out(), [(600, 1000, 10)])

    def test_event_bridging_clips_merges_all(self):
        reel = Reel(500, 10, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 30, 1000)
        reel.submit("e3", 20, 500)
        self.assertEqual(reel.clips_out(), [(0, 1000, 30)])


class QuotaTest(unittest.TestCase):
    def test_quota_drops_lowest_score(self):
        reel = Reel(100, 2, 0)
        reel.submit("e1", 5, 0)
        reel.submit("e2", 50, 1000)
        reel.submit("e3", 20, 2000)
        self.assertEqual(reel.count(), 2)
        self.assertEqual(reel.clips_out(),
                         [(1000, 1000, 50), (2000, 2000, 20)])

    def test_quota_tie_drops_later_start(self):
        reel = Reel(100, 2, 0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 10, 1000)
        reel.submit("e3", 20, 2000)
        self.assertEqual(reel.clips_out(),
                         [(0, 0, 10), (2000, 2000, 20)])

    def test_new_low_score_clip_can_be_evicted(self):
        reel = Reel(100, 1, 0)
        reel.submit("e1", 50, 0)
        reel.submit("e2", 10, 1000)
        self.assertEqual(reel.clips_out(), [(0, 0, 50)])


class DedupTest(unittest.TestCase):
    def test_same_event_id_counts_once(self):
        reel = Reel(100, 10, 0)
        self.assertTrue(reel.submit("same", 10, 0))
        self.assertFalse(reel.submit("same", 10, 5000))
        self.assertEqual(reel.count(), 1)

    def test_resubmitting_whole_sequence_is_stable(self):
        events = [("e1", 10, 0), ("e2", 20, 100), ("e3", 5, 5000)]
        reel = Reel(500, 10, 0)
        for _ in range(2):
            for event_id, score, at_ms in events:
                reel.submit(event_id, score, at_ms)
        self.assertEqual(reel.clips_out(),
                         [(0, 100, 20), (5000, 5000, 5)])


class OrderAndCostTest(unittest.TestCase):
    def test_output_sorted_by_start_for_unsorted_input(self):
        reel = Reel(100, 10, 0)
        reel.submit("e1", 10, 5000)
        reel.submit("e2", 20, 0)
        reel.submit("e3", 30, 2000)
        self.assertEqual(reel.clips_out(),
                         [(0, 0, 20), (2000, 2000, 30), (5000, 5000, 10)])

    def test_scanned_does_not_grow_linearly_with_clips(self):
        reel = Reel(1, 10000, 0)
        for index in range(3000):
            reel.submit("e-%d" % index, 10, index * 100)
        for _ in range(3000):
            reel.clips_out()
        self.assertLessEqual(reel.scanned_count(), 6000)


if __name__ == "__main__":
    unittest.main()
