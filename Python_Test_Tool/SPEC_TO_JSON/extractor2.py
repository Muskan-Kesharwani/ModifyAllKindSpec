import pandas as pd

def extract_universal_hierarchy(df):
    """Universal extractor that works with all Excel formats (JSON, IDOC, X12, EDIFACT)."""
    result = {}

    # Get column headers
    headers = df.columns.tolist()

    # Find Source Occurs column index
    source_occurs_idx = None
    for i, header in enumerate(headers):
        if 'Source Occurs' in str(header):
            source_occurs_idx = i
            break

    if source_occurs_idx is None:
        print("⚠️ Could not find 'Source Occurs' column")
        return {}

    # Input columns are everything before Source Occurs
    input_columns = headers[:source_occurs_idx]
    # Attribute columns are from Source Occurs onwards
    attribute_columns = headers[source_occurs_idx:]

    print(f"📊 Input columns: {input_columns}")
    print(f"📋 Attribute columns: {attribute_columns[:5]}...")  # Show first 5

    for _, row in df.iterrows():
        # Build element name from non-empty input columns
        element_parts = []
        for col in input_columns:
            value = str(row[col]).strip()
            if value and value != 'nan':
                element_parts.append(value)

        if not element_parts:
            continue  # Skip empty rows

        # Create element name (join with appropriate separator)
        element_name = element_parts[-1] if len(element_parts) == 1 else '/'.join(element_parts)

        # Extract all attributes
        attributes = {}
        for header in attribute_columns:
            value = str(row[header]).strip()
            if value and value != 'nan' and value != '':
                # Clean up ellipsis and special characters
                clean_value = value.replace("\u2026", "...")
                attributes[header] = clean_value

        if attributes:  # Only add if we have attributes
            result[element_name] = attributes

    return result

def extract_json_hierarchy(df):
    """Wrapper for JSON format - uses universal extractor."""
    return extract_universal_hierarchy(df)

def extract_edi_x12_hierarchy(df):
    """Wrapper for EDI-X12 format - uses universal extractor."""
    return extract_universal_hierarchy(df)

def extract_edifact_hierarchy(df):
    """Wrapper for EDIFACT format - uses universal extractor."""
    return extract_universal_hierarchy(df)

def extract_idoc_hierarchy(df):
    """Wrapper for IDOC format - uses universal extractor."""
    return extract_universal_hierarchy(df)
