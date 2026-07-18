#!/usr/bin/env python3
"""Download consecutive chunks of the public hard-unknot CSV.

Example:

    python download_hard_unknot_chunks.py --first 0 --count 10 --rows 5000

The script works with local paths and ``gs://`` paths understood by pandas/gcsfs.
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="gs://gdm-unknotting/hard_unknots.csv")
    parser.add_argument("--rows", type=int, default=5000, help="rows per chunk")
    parser.add_argument("--first", type=int, default=0, help="first chunk index")
    parser.add_argument("--count", type=int, default=10, help="number of chunks")
    parser.add_argument("--output-dir", default="hard_unknot_chunks")
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    wanted = set(range(args.first, args.first + args.count))
    made = []
    for chunk_index, frame in enumerate(pd.read_csv(args.source, chunksize=args.rows)):
        if chunk_index in wanted:
            start = chunk_index * args.rows
            end = start + len(frame) - 1
            path = output / f"hard_unknots_rows_{start}_{end}.csv.gz"
            frame.to_csv(path, index=False, compression="gzip")
            made.append(path)
            print(f"wrote {path} ({len(frame)} rows)")
        if chunk_index >= args.first + args.count - 1:
            break
    if len(made) != args.count:
        raise RuntimeError(f"requested {args.count} chunks but wrote {len(made)}")
    archive = output / f"hard_unknots_chunks_{args.first}_to_{args.first + args.count - 1}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        for path in made:
            handle.write(path, path.name)
    print(f"wrote {archive}")


if __name__ == "__main__":
    main()
