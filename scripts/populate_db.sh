#!/bin/bash

# Initialize micromamba if not already done
eval "$(micromamba shell hook --shell bash)"

# Activate the environment
micromamba activate rl4mm

cd ~/rl4mm/rl4mm/database && \
python3 populate_database.py \
  --min_trading_date "2012-06-21" \
  --max_trading_date "2012-06-21" \
  --path_to_lobster_data "../../test_data" \
  --book_snapshot_freq "S" \
  --max_rows 1000 \
  --ticker MSFT