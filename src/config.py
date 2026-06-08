from pathlib import Path

# Project root = two levels up from this file (src/config.py -> root)
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Ensure folders exist at import time
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]