import argparse
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

DEVICES = ["tv", "mobile", "web", "console"]
DEVICE_WEIGHTS = [0.55, 0.25, 0.15, 0.05]

# Explicit types, so nothing is guessed (one reason Parquet beats CSV)
SCHEMA = pa.schema([
    ("event_id", pa.string()),
    ("user_id", pa.int64()),
    ("title_id", pa.int32()),
    ("device", pa.string()),
    ("start_ts", pa.timestamp("ms")),
    ("end_ts", pa.timestamp("ms")),
])


def generate_events(rows, date, seed, n_users=100_000, n_titles=2_000):
    rng = np.random.default_rng(seed)  # same seed = same data every time

    user_id = rng.integers(1, n_users + 1, size=rows)

    # Skewed popularity: a few titles get most views (you'll need this in Week 9)
    ranks = np.arange(1, n_titles + 1)
    weights = 1 / ranks**1.1
    title_id = rng.choice(ranks, size=rows, p=weights / weights.sum()).astype("int32")

    device = rng.choice(DEVICES, size=rows, p=DEVICE_WEIGHTS)

    # Start times spread across the day; viewing lasts 1 to 240 minutes
    day_start = np.datetime64(date, "ms")
    offset_ms = rng.integers(0, 24 * 60 * 60 * 1000, size=rows)
    start_ts = day_start + offset_ms.astype("timedelta64[ms]")
    duration_ms = (np.clip(rng.exponential(35, size=rows), 1, 240) * 60_000).astype("int64")
    end_ts = start_ts + duration_ms.astype("timedelta64[ms]")

    event_id = [f"{date}-{seed}-{i}" for i in range(rows)]

    return pa.table(
        {
            "event_id": event_id,
            "user_id": user_id,
            "title_id": title_id,
            "device": device,
            "start_ts": start_ts,
            "end_ts": end_ts,
        },
        schema=SCHEMA,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate fake viewing events")
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="data/raw/events")
    args = parser.parse_args()

    # One folder per day: the start of partitioning (Week 6)
    out_dir = Path(args.out) / f"date={args.date}"
    out_dir.mkdir(parents=True, exist_ok=True)

    table = generate_events(args.rows, args.date, args.seed)
    pq.write_table(table, out_dir / "events.parquet", compression="zstd")
    print(f"Wrote {table.num_rows:,} rows to {out_dir / 'events.parquet'}")


if __name__ == "__main__":
    main()