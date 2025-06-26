#!/bin/bash

# Initialize micromamba if not already done
eval "$(micromamba shell hook --shell bash)"

# Activate the environment
micromamba activate rl4mm

cd ~/rl4mm/rl4mm/database && \
python3 populate_database.py \
  --path_to_lobster_data "../../test_data" \
  --book_snapshot_freq "S" \
  --max_rows 1000 \
  --ticker MSFT \
  --infer_dates_from_files