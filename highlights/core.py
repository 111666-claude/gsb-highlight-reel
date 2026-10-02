"""精彩镜头：评分筛选、相邻合并、配额与事件去重。

缺陷：合并边界用严格小于、合并后分数不取最大、配额不生效、不去重、
每次取片段都重新排序并全量扫描。
"""


class Reel:
    """精彩片段台账。"""

    def __init__(self, merge_ms, quota, min_score):
        self.merge_ms = merge_ms
        self.quota = quota
        self.min_score = min_score
        self.clips = []
        self.seen = set()
        self.scanned = 0

    def submit(self, event_id, score, at_ms):
        """提交一个高分事件。"""
        self.scanned += len(self.clips)
        if score < self.min_score:
            return False
        self.seen.add(event_id)
        for clip in self.clips:
            if at_ms - clip["end"] < self.merge_ms:
                if at_ms > clip["end"]:
                    clip["end"] = at_ms
                return True
        self.clips.append({"start": at_ms, "end": at_ms, "score": score})
        return True

    def clips_out(self):
        """按开始时间升序返回片段。"""
        self.scanned += len(self.clips)
        ordered = sorted(self.clips, key=lambda clip: clip["start"])
        return [(clip["start"], clip["end"], clip["score"]) for clip in ordered]

    def count(self):
        return len(self.clips)

    def scanned_count(self):
        return self.scanned
