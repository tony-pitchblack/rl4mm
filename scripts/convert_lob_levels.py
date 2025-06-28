#!/usr/bin/env python
"""Download LOB level parquet files from Hugging Face and convert them to
LOBSTER style CSV files.

The resulting files mirror the naming convention used in the ``test_data``
directory and can be fed into ``populate_database.py``.
"""
import argparse
import os
from pathlib import Path

import pandas as pd
from huggingface_hub import login, snapshot_download

DEFAULT_ORG_NAME = "TheNewMarketMakers"
DEFAULT_DATASET_NAME = "LOB_levels"


def convert_parquet_to_lobster(src: Path, dst_dir: Path, top_k: int) -> None:
    """Convert one parquet snapshot file to a CSV in LOBSTER format."""
    df = pd.read_parquet(src)
    if df.index.name is None:
        df.index.name = "timestamp"
    df = df.reset_index()

    rename_cols = {}
    for level in range(top_k):
        rename_cols.update(
            {
                f"sell_price_{level}": f"ask_price_{level + 1}",
                f"sell_volume_{level}": f"ask_size_{level + 1}",
                f"buy_price_{level}": f"bid_price_{level + 1}",
                f"buy_volume_{level}": f"bid_size_{level + 1}",
            }
        )
    df = df.rename(columns=rename_cols)

    book_cols = []
    for level in range(top_k):
        book_cols.extend(
            [
                f"ask_price_{level + 1}",
                f"ask_size_{level + 1}",
                f"bid_price_{level + 1}",
                f"bid_size_{level + 1}",
            ]
        )
    out_cols = ["timestamp"] + book_cols
    out_path = dst_dir / f"{src.stem}.csv"
    df[out_cols].to_csv(out_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert LOB levels downloaded from HF into LOBSTER CSV files"
    )
    parser.add_argument(
        "--folder_name", required=True, help="folder inside the dataset"
    )
    parser.add_argument(
        "--freq", type=int, default=15, help="snapshot frequency in seconds"
    )
    parser.add_argument("--top_k", type=int, default=10, help="number of levels")
    parser.add_argument("--org", default=DEFAULT_ORG_NAME, help="HF organisation")
    parser.add_argument(
        "--dataset", default=DEFAULT_DATASET_NAME, help="HF dataset name"
    )
    parser.add_argument(
        "--output", default="lobster_output", help="directory for CSV files"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("HF_TOKEN"),
        help="Hugging Face token with access to the dataset",
    )
    args = parser.parse_args()

    if args.token:
        login(args.token)

    lob_levels_dir = snapshot_download(
        repo_id=f"{args.org}/{args.dataset}",
        repo_type="dataset",
        local_dir="LOB_levels",
        allow_patterns=[
            f"{args.folder_name}/**/*{args.top_k}_levels.{args.freq}_sec*.parquet"
        ],
    )

    levels_root = Path(lob_levels_dir) / args.folder_name
    parquet_paths = sorted(
        levels_root.rglob(f"*{args.top_k}_levels.{args.freq}_sec*.parquet")
    )

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in parquet_paths:
        convert_parquet_to_lobster(Path(p), out_dir, args.top_k)
        print(f"Converted {p} -> {out_dir / (p.stem + '.csv')}")


if __name__ == "__main__":
    main()
