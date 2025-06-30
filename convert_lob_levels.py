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
from dotenv import load_dotenv
from collections import defaultdict
import pyarrow.parquet as pq
from tqdm import tqdm

load_dotenv()

# Defaults pulled from environment (fallback to original values)
DEFAULT_ORG_NAME = os.getenv("HF_ORG_NAME", "TheNewMarketMakers")
DEFAULT_LOB_LEVELS_DATASET_NAME = os.getenv("HF_LOB_LEVELS_DATASET_NAME", "LOB_levels")
DEFAULT_MBO_DATASET_NAME = os.getenv("HF_MBO_DATASET_NAME", "MBO_data")

def convert_parquet_to_lobster(src: Path, dst_dir: Path, top_k: int) -> None:
    """Convert LOB levels to LOBSTER format."""
    df = pd.read_parquet(src)
    if df.index.name is None:
        df.index.name = "timestamp"
    df = df.reset_index()

    # First, if the reset index produced the default "index" column rename it.
    if "index" in df.columns:
        df = df.rename(columns={"index": "timestamp"})

    # If still missing, try common alternative timestamp column names
    if "timestamp" not in df.columns:
        for alt in ("ts_idx", "ts_recv", "ts_event", "ts", "timestamp_ns"):
            if alt in df.columns:
                df = df.rename(columns={alt: "timestamp"})
                break

    # Final generic fallback using substring search
    if "timestamp" not in df.columns:
        time_like_cols = [c for c in df.columns if "time" in c.lower()]
        if time_like_cols:
            df = df.rename(columns={time_like_cols[0]: "timestamp"})

    # At this point we must have a timestamp column; if not, raise an error early
    if "timestamp" not in df.columns:
        raise KeyError("A 'timestamp' column could not be inferred from the parquet file. Available columns: "
                       f"{list(df.columns)}")

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
    price_cols = []
    size_cols = []
    for level in range(top_k):
        book_cols.extend(
            [
                f"ask_price_{level + 1}",
                f"ask_size_{level + 1}",
                f"bid_price_{level + 1}",
                f"bid_size_{level + 1}",
            ]
        )
        price_cols.extend([f"ask_price_{level + 1}", f"bid_price_{level + 1}"])
        size_cols.extend([f"ask_size_{level + 1}", f"bid_size_{level + 1}"])
    out_cols = book_cols

    # ------------------------------------------------------------------
    # Format adjustments – match LOBSTER sample (int prices * 10_000, int sizes)
    # ------------------------------------------------------------------
    df[price_cols] = (df[price_cols] * 10_000).round().astype("int32")
    df[size_cols] = df[size_cols].fillna(0).astype("int32")
    df["timestamp"] = df["timestamp"].astype("float64")  # timestamps kept as float seconds/ns

    out_path = dst_dir / f"{src.stem}.csv"
    df[out_cols].to_csv(out_path, index=False, header=False)


def list_dataset_folders(org: str, dataset: str, token: str | None = None) -> list[str]:
    """Return list of top-level folders in the specified Hugging Face dataset."""
    from huggingface_hub import HfFileSystem

    fs = HfFileSystem(token=token)
    repo_root = f"datasets/{org}/{dataset}"
    entries = fs.ls(repo_root, detail=True)

    # Keep only directories at the dataset root
    return [Path(e["name"]).name for e in entries if e.get("type") == "directory"]


def convert_mbo_parquet_to_lobster(src: Path, dst_dir: Path, top_k: int | None = None) -> None:
    """Convert MBO message parquet to LOBSTER *message* CSV format.

    Output columns (no header/index):
        time_sec, event_type, order_id, size, price_int, direction
    where
        - time_sec: seconds since midnight with fractional part (float)
        - event_type: 1 Add, 2 Modify, 3 Cancel, 4 Execute, 5 Delete
        - direction: 1 Buy, -1 Sell
    """

    mapping_event = {
        "A": 1,
        "M": 2,
        "C": 3,
        "F": 4,
        "E": 4,
        "T": 4,
        "D": 5,
    }

    mapping_side = {"B": 1, "A": -1}

    pf = pq.ParquetFile(src)
    out_path = dst_dir / f"{src.stem}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as f_out:
        for rg_idx in range(pf.num_row_groups):
            batch = pf.read_row_group(
                rg_idx,
                columns=["ts_recv", "action", "side", "price", "size", "order_id"],
            ).to_pandas()

            # In some parquet files `ts_recv` is stored as the index.
            if "ts_recv" not in batch.columns:
                if batch.index.name == "ts_recv":
                    batch = batch.reset_index()
                else:
                    # fallback: take index values regardless of name
                    batch = batch.reset_index().rename(columns={batch.columns[0]: "ts_recv"})

            ts_ns = batch["ts_recv"].astype("int64")
            batch["time"] = ((ts_ns / 1e9) % 86400).astype("float64")

            batch["event_type"] = batch["action"].map(mapping_event).astype("int8")
            batch["direction"] = batch["side"].map(mapping_side).astype("int8")

            batch["price_int"] = (batch["price"] * 10_000).round().astype("int32")

            out_cols = ["time", "event_type", "order_id", "size", "price_int", "direction"]

            batch[out_cols].to_csv(
                f_out,
                header=False,
                index=False,
                float_format="%.8f",
                lineterminator="\n",
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert LOB levels downloaded from HF into LOBSTER CSV files"
    )
    parser.add_argument(
        "--folder_name", help="folder inside the dataset (default: first folder in repo)"
    )
    parser.add_argument(
        "--freq", type=int, default=15, help="dataset frequency in seconds"
    )
    parser.add_argument("--top_k", type=int, default=10, help="number of levels")
    parser.add_argument("--org", default=DEFAULT_ORG_NAME, help="HF organisation")
    parser.add_argument(
        "--dataset", default=DEFAULT_LOB_LEVELS_DATASET_NAME, help="HF dataset name"
    )
    parser.add_argument(
        "--mbo_dataset", default=DEFAULT_MBO_DATASET_NAME, help="HF MBO dataset name"
    )
    parser.add_argument(
        "--output", default="data/LOBSTER_MBO_LOB_levels", help="directory for CSV files"
    )
    args = parser.parse_args()

    token = os.getenv("HF_TOKEN")
    if token:
        login(token)

    folder_name = args.folder_name
    if folder_name is None:
        available_folders = list_dataset_folders(args.org, args.dataset, token)
        if not available_folders:
            raise ValueError(f"No folders found in dataset {args.org}/{args.dataset}")
        folder_name = available_folders[0]
        print(f"No --folder_name provided. Using '{folder_name}'.")

    lob_levels_dir = snapshot_download(
        repo_id=f"{args.org}/{args.dataset}",
        repo_type="dataset",
        local_dir="data/LOB_levels",
        allow_patterns=[
            f"{folder_name}/**/*{args.top_k}_levels.{args.freq}_sec*.parquet"
        ],
        token=token,
    )

    levels_root = Path(lob_levels_dir) / folder_name
    parquet_paths = sorted(
        levels_root.rglob(f"*{args.top_k}_levels.{args.freq}_sec*.parquet")
    )

    out_dir = Path(args.output)
    for p in tqdm(parquet_paths, desc="Levels", unit="file"):
        # Preserve sub-directory structure relative to the selected folder
        rel_path = Path(p).relative_to(levels_root)  # e.g. glbx-mdp3-20250328/filename.parquet
        target_dir = out_dir / folder_name / rel_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        convert_parquet_to_lobster(Path(p), target_dir, args.top_k)

        print(f"\nConverted {p}\nto output:{target_dir / (p.stem + '.csv')}")

    # ------------------------------------------------------------------
    # Download and group MBO files alongside the converted LOB outputs
    # ------------------------------------------------------------------
    mbo_dataset = args.mbo_dataset
    if mbo_dataset:
        mbo_dir = snapshot_download(
            repo_id=f"{args.org}/{mbo_dataset}",
            repo_type="dataset",
            local_dir="data/MBO",
            allow_patterns=[f"{folder_name}/**/*{args.freq}_sec*.parquet"],
            token=token,
        )

        mbo_root = Path(mbo_dir) / folder_name
        mbo_paths = sorted(mbo_root.rglob(f"*{args.freq}_sec*.parquet"))

        for mbo_path in tqdm(mbo_paths, desc="MBO", unit="file"):
            rel_path = mbo_path.relative_to(mbo_root)
            target_dir = out_dir / folder_name / rel_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)

            # Convert MBO parquet (messages) to LOBSTER order-book CSV format
            convert_mbo_parquet_to_lobster(mbo_path, target_dir, args.top_k)

            print(
                f"\nConverted MBO {mbo_path}\n to output:{target_dir / (mbo_path.stem + '.csv')}"
            )


if __name__ == "__main__":
    main() 