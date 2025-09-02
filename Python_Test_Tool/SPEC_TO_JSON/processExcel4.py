import os
import json
import pandas as pd
from extractor4 import extract_json_hierarchy, extract_edi_x12_hierarchy, extract_edifact_hierarchy, extract_idoc_hierarchy, extract_universal_hierarchy
from detector import detect_format

# Get the current script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the relative path to config.json
CONFIG_PATH = os.path.join(BASE_DIR, "..", "config", "config.json")

# Load Config
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Read paths from config and make them absolute from project root
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
INPUT_PATH = os.path.join(ROOT_DIR, config["input_path"])
OUTPUT_PATH = os.path.join(ROOT_DIR, config["output_path"])

print(f"📂 Input Path: {INPUT_PATH}")
print(f"📂 Output Path: {OUTPUT_PATH}")

def find_data_sheet_and_row(file_path):
    """Automatically finds the correct sheet and starting row for data extraction."""
    xls = pd.ExcelFile(file_path)

    # Look for sheets that contain mapping data (usually have "ToCanonical" or similar)
    mapping_sheets = []
    for sheet_name in xls.sheet_names:
        if any(keyword in sheet_name.lower() for keyword in ['tocanonical', 'mapping', 'transform', '(t)']):
            mapping_sheets.append(sheet_name)

    # If no specific mapping sheets found, try all sheets
    if not mapping_sheets:
        mapping_sheets = xls.sheet_names

    # Search for the "Source Occurs" column in each sheet
    for sheet_name in mapping_sheets:
        try:
            # Read the entire sheet to find the header row
            full_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

            # Search for "Source Occurs" text
            for i, row in full_df.iterrows():
                if any('Source Occurs' in str(cell) for cell in row if pd.notna(cell)):
                    print(f"📍 Found data structure in sheet '{sheet_name}' at row {i}")
                    return sheet_name, i

        except Exception as e:
            print(f"⚠️ Error reading sheet '{sheet_name}': {e}")
            continue

    # Fallback to original method if nothing found
    print("⚠️ Could not auto-detect data location, using default (sheet 2, skip 13)")
    return 2, 13

def process_excel():
    """Reads Excel file and generates JSON based on format detection."""
    # Auto-detect the correct sheet and starting row
    sheet_name, skip_rows = find_data_sheet_and_row(INPUT_PATH)

    df = pd.read_excel(INPUT_PATH, sheet_name=sheet_name, skiprows=skip_rows, dtype=str, engine="openpyxl")
    df.fillna("", inplace=True)

    print(f"📊 Processing sheet: {sheet_name}, starting from row: {skip_rows}")
    print(f"📋 Data shape: {df.shape}")
    print(f"📝 Columns found: {list(df.columns)[:10]}")

    detected_format = detect_format(df, INPUT_PATH)

    # Select the correct extractor function
    extractors = {
        "JSON": extract_json_hierarchy,
        "EDI-X12": extract_edi_x12_hierarchy,
        "EDIFACT": extract_edifact_hierarchy,
        "IDOC": extract_idoc_hierarchy,
    }

    print(f"🔍 Using {detected_format} extractor...")

    # Use universal extractor as fallback or primary
    try:
        if detected_format in extractors:
            hierarchy = extractors[detected_format](df)
        else:
            print("⚠️ Using universal extractor as fallback")
            hierarchy = extract_universal_hierarchy(df)
    except Exception as e:
        print(f"❌ Error with specific extractor: {e}")
        print("🔄 Falling back to universal extractor...")
        hierarchy = extract_universal_hierarchy(df)

    print(f"📊 Extracted {len(hierarchy)} top-level elements")

    # Save output
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    output_file = os.path.join(OUTPUT_PATH, f"{detected_format}_structure.json")

    final_output = {
        "format": detected_format,
        "total_elements": len(hierarchy),
        "hierarchy": hierarchy
    }

    with open(output_file, "w") as f:
        json.dump(final_output, f, indent=4)

    print(f"✅ Processed and saved: {output_file}")

    # Show a sample of what was extracted
    print("\n📋 Sample of extracted structure:")
    sample_keys = list(hierarchy.keys())[:3]
    for key in sample_keys:
        print(f"  - {key}: {type(hierarchy[key])}")
        if isinstance(hierarchy[key], dict) and "source_path" in hierarchy[key]:
            print(f"    Source Path: {hierarchy[key]['source_path']}")

    if len(hierarchy) > 3:
        print(f"  ... and {len(hierarchy) - 3} more elements")

if __name__ == "__main__":
    process_excel()
