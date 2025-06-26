# Database Setup and Population Scripts

This directory contains scripts to set up and populate the PostgreSQL database with LOBSTER data.

## What was Fixed

1. **Date Inference**: Modified `populate_database.py` to automatically infer trading dates from LOBSTER filenames
2. **Level Inference**: Added automatic inference of `n_levels` from LOBSTER filenames  
3. **Database Configuration**: Created proper `.env` file and database setup
4. **Script Integration**: Created comprehensive setup scripts that handle the full workflow

## Available Scripts

### Core Scripts

- **`setup_and_populate_db.sh`**: Complete setup - runs all steps in order
- **`populate_db.sh`**: Populate database with LOBSTER data (auto-infers dates and levels)
- **`clear_db.sh`**: Clear all data from the database
- **`test_db.sh`**: Test database connection and view sample data

### Database Setup Scripts

- **`create_admin_user.sh`**: Create PostgreSQL admin user
- **`create_db.sh`**: Create the `lob_snapshots` database

## Usage

### Quick Start
```bash
# Complete setup from scratch
scripts/setup_and_populate_db.sh
```

### Individual Steps
```bash
# 1. Set up database (one time only)
scripts/create_admin_user.sh
scripts/create_db.sh

# 2. Populate with data
scripts/populate_db.sh

# 3. Test the setup
scripts/test_db.sh
```

### Clear and Repopulate
```bash
scripts/clear_db.sh
scripts/populate_db.sh
```

## Configuration

The scripts automatically:
- Infer trading dates from LOBSTER filenames (e.g., `MSFT_2012-06-21_*`)
- Infer number of levels from filenames (e.g., `*_orderbook_10.csv`)
- Use the `test_data/` directory for LOBSTER files
- Limit to 1000 rows for testing (configurable in `populate_db.sh`)

## Database Details

- **Host**: localhost:5432
- **Database**: lob_snapshots  
- **User**: admin
- **Password**: admin
- **Tables**: `book`, `messages`

## Environment

The scripts use micromamba environment `rl4mm` and require:
- PostgreSQL running locally
- Python environment with required packages
- LOBSTER data files in `test_data/` directory

## Sample Output

After successful population:
- ~1000 message records
- ~9 book snapshot records  
- Data for MSFT on 2012-06-21 