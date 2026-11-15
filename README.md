# Netflix viewing platform

A mini version of a streaming platform's viewing-data pipeline, built week by week as I learn data engineering.

This first piece generates fake viewing events and stores them as Parquet. Later stages will process them with Spark, stream them through Kafka, load them into Iceberg tables, and add quality checks and monitoring.

## What the generator produces

One row per viewing event:

| Column | Type | Notes |
|---|---|---|
| `event_id` | string | Unique ID for the event |
| `user_id` | int64 | 100,000 users |
| `title_id` | int32 | 2,000 titles with skewed popularity: the top 10 titles get about 45% of views |
| `device` | string | tv 55%, mobile 25%, web 15%, console 5% |
| `start_ts` | timestamp (ms) | Spread across the day |
| `end_ts` | timestamp (ms) | 1 to 240 minutes after the start |

Output is written to one folder per day: `data/raw/events/date=YYYY-MM-DD/events.parquet`. The same seed always produces the same data.

## How to run it

You need [uv](https://docs.astral.sh/uv/) installed.

```bash
git clone https://github.com/<your-username>/netflix-viewing-platform.git
cd netflix-viewing-platform
uv sync
uv run python generate_events.py --date 2026-11-14
```

Options:

- `--rows`: number of events (default 1,000,000)
- `--date`: the day to generate, in YYYY-MM-DD format (required)
- `--seed`: random seed (default 42)
- `--out`: output folder (default `data/raw/events`)

## Parquet vs CSV

`compare_formats.py` writes the same 1 million rows as CSV, then times reading only the `title_id` column from each file.

```bash
uv run python compare_formats.py
```

| Format | File size | Time to read `title_id` |
|---|---|---|
| Parquet (zstd) | [12.6] MB | [0.014] s |
| CSV | [82.1] MB | [0.425] s |

Parquet was about [6]× smaller and [30]× faster to read here. It stores data by column, so the reader fetches only `title_id` and skips the other five columns. Each column is also encoded and compressed separately, which shrinks repeated values like `device` and `title_id`. CSV has to be read and parsed in full, row by row, to pull out one column.