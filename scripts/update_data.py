#!/usr/bin/env python3
"""
Standalone script for incremental data update. Suitable for cron/scheduled runs.
Usage: python scripts/update_data.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_pipeline.data_updater import update_data
from core.config import TICKERS, FORWARD_RETURN_PERIOD


def main():
    print("Running incremental data update...")
    bundle = update_data(
        tickers=TICKERS,
        forward_period=FORWARD_RETURN_PERIOD,
    )
    print(f"Done: {bundle.close_df.shape[0]} days, {bundle.close_df.shape[1]} tickers")


if __name__ == "__main__":
    main()
