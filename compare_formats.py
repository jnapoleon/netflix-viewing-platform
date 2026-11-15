import time
from pathlib import Path

import pandas as pd

parquet_path = Path("data/raw/events/date=2026-11-14/events.parquet")
csv_path = Path("data/events.csv")

pd.read_parquet(parquet_path).to_csv(csv_path, index=False)

def mb(path):
    return path.stat().st_size / 1_000_000

start = time.perf_counter()
pd.read_parquet(parquet_path, columns=["title_id"])
parquet_secs = time.perf_counter() - start

start = time.perf_counter()
pd.read_csv(csv_path, usecols=["title_id"])
csv_secs = time.perf_counter() - start

print(f"Parquet: {mb(parquet_path):.1f} MB, read title_id in {parquet_secs:.3f}s")
print(f"CSV:     {mb(csv_path):.1f} MB, read title_id in {csv_secs:.3f}s")