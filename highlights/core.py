"""精彩镜头：评分筛选、相邻合并、配额与事件去重。

片段保存在一棵按开始时间排序的 treap 里：提交时 O(log n) 定位左右相邻
片段完成合并，配额用惰性删除的堆维护，取片段直接返回升序缓存，不做
全量重排，scanned_count 只统计合并时实际查看的相邻片段。
"""

import heapq
import random


class _Node:
    __slots__ = ("start", "end", "score", "prio", "left", "right", "version")

    def __init__(self, start, score):
        self.start = start
        self.end = start
        self.score = score
        self.prio = random.random()
        self.left = None
        self.right = None
        self.version = 0


def _rotate_right(node):
    child = node.left
    node.left = child.right
    child.right = node
    return child


def _rotate_left(node):
    child = node.right
    node.right = child.left
    child.left = node
    return child


def _insert(node, fresh):
    if node is None:
        return fresh
    if fresh.start < node.start:
        node.left = _insert(node.left, fresh)
        if node.left.prio < node.prio:
            node = _rotate_right(node)
    else:
        node.right = _insert(node.right, fresh)
        if node.right.prio < node.prio:
            node = _rotate_left(node)
    return node


def _delete(node, start):
    if node.start == start:
        return _merge(node.left, node.right)
    if start < node.start:
        node.left = _delete(node.left, start)
    else:
        node.right = _delete(node.right, start)
    return node


def _merge(left, right):
    if left is None:
        return right
    if right is None:
        return left
    if left.prio < right.prio:
        left.right = _merge(left.right, right)
        return left
    right.left = _merge(left, right.left)
    return right


def _predecessor(node, start):
    """开始时间严格小于 start 的最靠右片段。"""
    found = None
    while node is not None:
        if node.start < start:
            found = node
            node = node.right
        else:
            node = node.left
    return found


def _successor(node, start):
    """开始时间大于等于 start 的最靠左片段。"""
    found = None
    while node is not None:
        if node.start >= start:
            found = node
            node = node.left
        else:
            node = node.right
    return found


class Reel:
    """精彩片段台账。"""

    def __init__(self, merge_ms, quota, min_score):
        self.merge_ms = merge_ms
        self.quota = quota
        self.min_score = min_score
        self._root = None
        self._size = 0
        self._cache = []
        self._dirty = False
        self.seen = set()
        self.scanned = 0
        self._heap = []  # (score, -start, version, start)，惰性删除
        self._version = 0

    def submit(self, event_id, score, at_ms):
        """提交一个高分事件；同一 event_id 重复提交幂等。"""
        if event_id in self.seen:
            return True
        if score < self.min_score:
            return False
        self.seen.add(event_id)

        left = _predecessor(self._root, at_ms)
        right = _successor(self._root, at_ms)

        merged = None
        if left is not None:
            self.scanned += 1
            if at_ms - left.end <= self.merge_ms:
                merged = left
        if right is not None:
            self.scanned += 1
            if right.start - at_ms <= self.merge_ms:
                if merged is None:
                    merged = right
                else:
                    # 事件把左右两段桥接成一段
                    merged.end = max(merged.end, right.end)
                    merged.score = max(merged.score, right.score)
                    self._root = _delete(self._root, right.start)
                    self._size -= 1
        if merged is not None:
            if merged is right and at_ms < merged.start:
                self._root = _delete(self._root, merged.start)
                merged.start = at_ms
                merged.left = None
                merged.right = None
                self._root = _insert(self._root, merged)
            merged.end = max(merged.end, at_ms)
            merged.score = max(merged.score, score)
            self._push(merged)
        else:
            self._root = _insert(self._root, _Node(at_ms, score))
            self._size += 1
            self._push(self._find(at_ms))

        self._dirty = True
        self._enforce_quota()
        return True

    def _find(self, start):
        node = self._root
        while node is not None and node.start != start:
            node = node.left if start < node.start else node.right
        return node

    def _push(self, node):
        self._version += 1
        node.version = self._version
        heapq.heappush(self._heap, (node.score, -node.start, self._version, node.start))

    def _enforce_quota(self):
        """片段数超过 quota 时丢分数最低的，同分先丢开始时间晚的。"""
        while self._size > self.quota:
            _, _, version, start = heapq.heappop(self._heap)
            node = self._find(start)
            if node is None or node.version != version:
                continue
            self._root = _delete(self._root, start)
            self._size -= 1

    def _rebuild(self):
        ordered = []

        def walk(node):
            if node is None:
                return
            walk(node.left)
            ordered.append((node.start, node.end, node.score))
            walk(node.right)

        walk(self._root)
        self._cache = ordered
        self._dirty = False

    def clips_out(self):
        """按开始时间升序返回片段；结构未变时直接返回缓存，不重排。"""
        if self._dirty:
            self._rebuild()
        return self._cache

    def count(self):
        return self._size

    def scanned_count(self):
        return self.scanned
