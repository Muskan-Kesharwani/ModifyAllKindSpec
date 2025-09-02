
import pandas as pd

class HierarchyBuilder:
    """Separate class to handle hierarchy building with source path tracking."""

    def __init__(self):
        self.element_counter = {}  # Track duplicate elements

    def add_element(self, result, hierarchy_path, element_name, attributes, source_path):
        """Add element to hierarchy with source path and handle duplicates."""

        # Create unique key for duplicate tracking
        unique_key = f"{'/'.join(hierarchy_path)}/{element_name}" if hierarchy_path else element_name

        # Track element occurrences
        if unique_key not in self.element_counter:
            self.element_counter[unique_key] = 0
        self.element_counter[unique_key] += 1

        # Create element name with occurrence number if duplicate
        if self.element_counter[unique_key] > 1:
            final_element_name = f"{element_name}_occurrence_{self.element_counter[unique_key]}"
        else:
            final_element_name = element_name

        # Navigate to the correct level in hierarchy
        current_level = result
        for level in hierarchy_path:
            if level not in current_level:
                current_level[level] = {}
            current_level = current_level[level]

        # Add the element with source path
        if final_element_name not in current_level:
            current_level[final_element_name] = {}

        # Add source path as a special attribute
        current_level[final_element_name]["source_path"] = source_path

        # Add all other attributes
        current_level[final_element_name].update(attributes)

        return final_element_name

def extract_json_hierarchy(df):
    """Enhanced JSON hierarchy extraction with source path tracking."""
    hierarchy_builder = HierarchyBuilder()
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

    print(f"📊 Input hierarchy columns: {input_columns}")
    print(f"📋 Attribute columns: {attribute_columns[:5]}...")

    for row_idx, row in df.iterrows():
        # Build hierarchy path and element name from non-empty input columns
        hierarchy_parts = []
        source_path_parts = []

        for col in input_columns:
            value = str(row[col]).strip()
            if value and value != 'nan' and value.lower() not in ['', 'null']:
                hierarchy_parts.append(value)
                source_path_parts.append(value)

        if not hierarchy_parts:
            print(f"⚠️ Skipping row {row_idx}: No valid hierarchy elements")
            continue

        # Build source path
        source_path = "/" + "/".join(source_path_parts)

        # The last part is the element name, everything before is hierarchy
        if len(hierarchy_parts) >= 1:
            element_name = hierarchy_parts[-1]
            hierarchy_path = hierarchy_parts[:-1]
        else:
            element_name = hierarchy_parts[0]
            hierarchy_path = []

        # Extract attributes
        attributes = {}
        for header in attribute_columns:
            if pd.notna(row[header]) and str(row[header]).strip():
                clean_value = str(row[header]).strip().replace("\u2026", "...")
                if clean_value.lower() not in ['', 'null', 'nan']:
                    attributes[header] = clean_value

        # Add element to hierarchy with source path
        final_element_name = hierarchy_builder.add_element(
            result, hierarchy_path, element_name, attributes, source_path
        )

        print(f"✅ Added: {'/'.join(hierarchy_path + [final_element_name])} -> {source_path}")

    return result

def extract_edi_x12_hierarchy(df):
    """Enhanced EDI-X12 hierarchy extraction with source path tracking."""
    hierarchy_builder = HierarchyBuilder()
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
        print("⚠️ Could not find 'Source Occurs' column for EDI-X12")
        return {}

    # Input columns are everything before Source Occurs
    input_columns = headers[:source_occurs_idx]
    attribute_columns = headers[source_occurs_idx:]

    for row_idx, row in df.iterrows():
        # Build segment hierarchy for EDI-X12
        segment_parts = []
        source_path_parts = []

        for col in input_columns:
            value = str(row[col]).strip()
            if value and value != 'nan' and value.lower() not in ['', 'null']:
                segment_parts.append(value)
                source_path_parts.append(value)

        if not segment_parts:
            continue

        # Build source path for EDI
        source_path = "*".join(source_path_parts)  # EDI uses * separator

        # For EDI, first part is usually segment ID
        segment_id = segment_parts[0]
        element_path = segment_parts[1:] if len(segment_parts) > 1 else []

        # Extract attributes
        attributes = {}
        for header in attribute_columns:
            if pd.notna(row[header]) and str(row[header]).strip():
                clean_value = str(row[header]).strip().replace("\u2026", "...")
                if clean_value.lower() not in ['', 'null', 'nan']:
                    attributes[header] = clean_value

        # Create element name from full path
        element_name = "_".join(segment_parts) if len(segment_parts) > 1 else segment_id

        # Add to hierarchy
        hierarchy_builder.add_element(
            result, [segment_id], element_name, attributes, source_path
        )

    return result

def extract_edifact_hierarchy(df):
    """Enhanced EDIFACT hierarchy extraction with source path tracking."""
    return extract_edi_x12_hierarchy(df)  # Similar structure to X12

def extract_idoc_hierarchy(df):
    """Enhanced IDOC hierarchy extraction with source path tracking."""
    hierarchy_builder = HierarchyBuilder()
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
        print("⚠️ Could not find 'Source Occurs' column for IDOC")
        return {}

    input_columns = headers[:source_occurs_idx]
    attribute_columns = headers[source_occurs_idx:]

    for row_idx, row in df.iterrows():
        # Build IDOC segment hierarchy
        idoc_parts = []
        source_path_parts = []

        for col in input_columns:
            value = str(row[col]).strip()
            if value and value != 'nan' and value.lower() not in ['', 'null']:
                idoc_parts.append(value)
                source_path_parts.append(value)

        if not idoc_parts:
            continue

        # Build source path for IDOC
        source_path = "/".join(source_path_parts)

        # For IDOC, typically segment/field structure
        segment_id = idoc_parts[0]
        element_path = idoc_parts[1:] if len(idoc_parts) > 1 else []

        # Extract attributes
        attributes = {}
        for header in attribute_columns:
            if pd.notna(row[header]) and str(row[header]).strip():
                clean_value = str(row[header]).strip().replace("\u2026", "...")
                if clean_value.lower() not in ['', 'null', 'nan']:
                    attributes[header] = clean_value

        # Create element name
        element_name = "_".join(idoc_parts) if len(idoc_parts) > 1 else segment_id

        # Add to hierarchy
        hierarchy_builder.add_element(
            result, [segment_id], element_name, attributes, source_path
        )

    return result

def extract_universal_hierarchy(df):
    """Universal extractor that works with all Excel formats with enhanced source path tracking."""
    hierarchy_builder = HierarchyBuilder()
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
    print(f"📋 Attribute columns: {attribute_columns[:5]}...")

    for row_idx, row in df.iterrows():
        # Build element path from non-empty input columns
        element_parts = []
        source_path_parts = []

        for col in input_columns:
            value = str(row[col]).strip()
            if value and value != 'nan' and value.lower() not in ['', 'null']:
                element_parts.append(value)
                source_path_parts.append(value)

        if not element_parts:
            print(f"⚠️ Skipping row {row_idx}: No valid elements")
            continue

        # Build source path
        source_path = "/" + "/".join(source_path_parts)

        # Create element name and hierarchy
        element_name = element_parts[-1] if len(element_parts) >= 1 else element_parts[0]
        hierarchy_path = element_parts[:-1] if len(element_parts) > 1 else []

        # Extract attributes
        attributes = {}
        for header in attribute_columns:
            if pd.notna(row[header]) and str(row[header]).strip():
                clean_value = str(row[header]).strip().replace("\u2026", "...")
                if clean_value.lower() not in ['', 'null', 'nan']:
                    attributes[header] = clean_value

        if attributes:  # Only add if there are attributes
            # Add element to hierarchy with source path tracking
            final_element_name = hierarchy_builder.add_element(
                result, hierarchy_path, element_name, attributes, source_path
            )

            print(f"✅ Row {row_idx}: Added {'/'.join(hierarchy_path + [final_element_name])} -> {source_path}")
        else:
            print(f"⚠️ Row {row_idx}: Skipping element '{element_name}' - no attributes found")

    return result
