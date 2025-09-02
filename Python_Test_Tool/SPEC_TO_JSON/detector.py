import json
import pandas as pd

import json
import os

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the relative path to config.json
CONFIG_PATH = os.path.join(BASE_DIR, "..", "config", "config.json")

# Load Config
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

print("🔧 Loaded Configuration:", config)

FORMAT_OVERRIDE = config.get("format_override", {})

# Predefined format indicators
JSON_FIELDS = {"data", "messageBody", "transactionSet", "document"}
EDI_X12_FIELDS = {"ISA01", "GS01", "ST01"}
EDIFACT_FIELDS = {"UNB01", "UNH01", "UNT01"}
IDOC_FIELDS = {"E1EDK01", "E1EDP01"}

def detect_format(df, input_path):
    """Detects file format based on first 10 column values."""
    row_values = df.iloc[:, :10].dropna().stack().unique()  # Extract unique values from A-J

    # Override if specified in config
    if input_path in FORMAT_OVERRIDE:
        return FORMAT_OVERRIDE[input_path]

    # Detection logic
    if any(field in row_values for field in EDI_X12_FIELDS):
        return "EDI-X12"
    elif any(field in row_values for field in EDIFACT_FIELDS):
        return "EDIFACT"
    elif any(field in row_values for field in IDOC_FIELDS):
        return "IDOC"
    else:
        return "JSON"
