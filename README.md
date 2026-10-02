# highlight-reel

精彩镜头：评分筛选、相邻合并、配额与事件去重，只用 Python 标准库。

```
python3 -m highlights.cli --sample merge
python3 -m highlights.cli --sample score
python3 -m highlights.cli --sample quota
python3 -m highlights.cli --sample dup
python3 -m highlights.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **筛选**：`score < min_score` 的事件直接丢弃。
- **合并**：新事件与已有片段的间隔不超过 `merge_ms` 时合并进该片段，
  间隔正好等于 `merge_ms` 也要合并；片段时间范围取并集，分数取最大值。
- **配额**：片段数超过 `quota` 时丢掉分数最低的；同分先丢开始时间晚的。
- **去重**：同一个 `event_id` 只算一次，重复提交不产生新片段。
- **顺序**：输出按开始时间升序。
- **代价**：取片段不许每次全量重排，`scanned_count` 不随片段数线性增长。
- **规模**：10 万事件、每秒 10 万次取片段，单次摊还 O(新增片段数)。

## 输出契约（不改格式）

```
clips=..
score=..
scanned=..
```

## 目录

```
highlights/core.py   筛选、合并、配额与去重
highlights/cli.py    命令行入口
tests/               unittest 用例
```
