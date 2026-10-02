"""精彩镜头：评分筛选、相邻合并、配额与事件去重。

片段始终按开始时间升序维护：提交时二分定位、就地合并，取片段不重排；
配额用小根堆（惰性删除）淘汰最低分片段；输出缓存至下次变更。
"""

import heapq
from bisect import bisect_left


class Reel:
    """精彩片段台账。"""

    def __init__(self, merge_ms, quota, min_score):
        self.merge_ms = merge_ms
        self.quota = quota
        self.min_score = min_score
        self.clips = []
        self.seen = set()
        self.scanned = 0
        self._starts = []
        self._heap = []
        self._alive = set()
        self._next_id = 0
        self._cache = []
        self._dirty = False

    def submit(self, event_id, score, at_ms):
        """提交一个高分事件；低于门槛或已受理的 event_id 直接忽略。"""
        if score < self.min_score:
            return False
        if event_id in self.seen:
            return False
        self.seen.add(event_id)

        pos = bisect_left(self._starts, at_ms)
        lo = pos
        while lo > 0:
            self.scanned += 1
            if self.clips[lo - 1]["end"] + self.merge_ms >= at_ms:
                lo -= 1
            else:
                break
        hi = pos
        while hi < len(self.clips):
            self.scanned += 1
            if self.clips[hi]["start"] - self.merge_ms <= at_ms:
                hi += 1
            else:
                break

        if lo < hi:
            self._merge_into(lo, hi, score, at_ms)
        else:
            self._insert_clip(pos, {"start": at_ms, "end": at_ms,
                                    "score": score, "_id": self._mint_id()})
        self._dirty = True
        self._enforce_quota()
        return True

    def _mint_id(self):
        clip_id = self._next_id
        self._next_id += 1
        return clip_id

    def _track(self, clip):
        self._alive.add(clip["_id"])
        heapq.heappush(self._heap,
                       (clip["score"], -clip["start"], clip["_id"]))

    def _insert_clip(self, pos, clip):
        self.clips.insert(pos, clip)
        self._starts.insert(pos, clip["start"])
        self._track(clip)

    def _merge_into(self, lo, hi, score, at_ms):
        group = self.clips[lo:hi]
        best = score
        for clip in group:
            self._alive.discard(clip["_id"])
            if clip["score"] > best:
                best = clip["score"]
        merged = {"start": min(group[0]["start"], at_ms),
                  "end": max(group[-1]["end"], at_ms),
                  "score": best,
                  "_id": self._mint_id()}
        self.clips[lo:hi] = [merged]
        self._starts[lo:hi] = [merged["start"]]
        self._track(merged)

    def _enforce_quota(self):
        while self.clips and len(self.clips) > self.quota:
            _, neg_start, clip_id = heapq.heappop(self._heap)
            if clip_id not in self._alive:
                continue
            self._alive.discard(clip_id)
            pos = bisect_left(self._starts, -neg_start)
            del self.clips[pos]
            del self._starts[pos]

    def clips_out(self):
        """按开始时间升序返回片段；结果缓存至下次变更，请勿修改返回值。"""
        if self._dirty:
            self._cache = [(clip["start"], clip["end"], clip["score"])
                           for clip in self.clips]
            self._dirty = False
        return self._cache

    def count(self):
        return len(self.clips)

    def scanned_count(self):
        return self.scanned
