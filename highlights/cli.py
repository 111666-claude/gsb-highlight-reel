"""命令行入口：跑精彩镜头样例。"""

import argparse

from .core import Reel


def build_parser():
    parser = argparse.ArgumentParser(prog="highlight-reel", description="精彩镜头")
    parser.add_argument("--sample", default="merge",
                        help="merge / score / quota / dup / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "merge":
        reel = Reel(merge_ms=500, quota=10, min_score=0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 500)
        print("clips=%d" % reel.count())
    elif args.sample == "score":
        reel = Reel(merge_ms=500, quota=10, min_score=0)
        reel.submit("e1", 10, 0)
        reel.submit("e2", 20, 100)
        out = reel.clips_out()
        print("score=%d" % out[0][2])
    elif args.sample == "quota":
        reel = Reel(merge_ms=100, quota=2, min_score=0)
        reel.submit("e1", 5, 0)
        reel.submit("e2", 50, 1000)
        reel.submit("e3", 20, 2000)
        print("clips=%d" % reel.count())
    elif args.sample == "dup":
        reel = Reel(merge_ms=100, quota=10, min_score=0)
        reel.submit("same", 10, 0)
        reel.submit("same", 10, 5000)
        print("clips=%d" % reel.count())
    elif args.sample == "scan":
        reel = Reel(merge_ms=1, quota=10000, min_score=0)
        for index in range(3000):
            reel.submit("e-%d" % index, 10, index * 100)
        for _ in range(3000):
            reel.clips_out()
        print("scanned=%d" % reel.scanned_count())
    else:
        raise SystemExit("需要 --sample merge|score|quota|dup|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
