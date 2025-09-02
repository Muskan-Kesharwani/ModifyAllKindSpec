#!/usr/bin/env python3
"""
Unified Test Generator for Missing Required/Optional Fields

This module generates test files by removing or commenting specific fields
based on their occurrence patterns (1...1 for required, 0...1 for optional).
Supports JSON, XML, EDI-X12, EDIFACT, and IDOC formats with field-level precision.
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Load configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")

with open(CONFIG_PATH, "r") as config_file:
    config_raw = json.load(config_file)

# Convert relative paths to absolute paths from project root
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
CONFIG = config_raw.copy()
CONFIG["spec_file"] = os.path.join(ROOT_DIR, config_raw["spec_file"])
CONFIG["max_file"] = os.path.join(ROOT_DIR, config_raw["max_file"])
CONFIG["output_directory"] = os.path.join(ROOT_DIR, config_raw["output_directory"])

# Ensure output directory exists
os.makedirs(CONFIG["output_directory"], exist_ok=True)

def detect_file_format(file_path):
    """Detect the format of the max file based on extension and content."""
    if file_path.endswith('.json'):
        return 'JSON'
    elif file_path.endswith('.xml'):
        return 'XML'
    elif file_path.endswith('.edi'):
        return 'EDI-X12'
    elif file_path.endswith('.txt'):
        # Check content for EDI/EDIFACT/IDOC patterns
        with open(file_path, 'r') as f:
            content = f.read(100)
            if content.startswith('UNA') or content.startswith('UNB'):
                return 'EDIFACT'
            elif 'ISA' in content or 'GS' in content:
                return 'EDI-X12'
            elif content.startswith('E1') or 'E1EDK' in content or 'E1EDP' in content:
                return 'IDOC'
    return 'UNKNOWN'

def find_fields_by_occurrence(spec_data, target_occurrence):
    """
    Find all fields with specific occurrence pattern.
    target_occurrence: '1...1' for required, '0...1' for optional
    """
    fields = []

    for element_name, attributes in spec_data.items():
        if element_name == "format":
            continue

        # Check Source Occurs for the pattern
        source_occurs = attributes.get("Source Occurs", "")
        if source_occurs == target_occurrence:
            fields.append({
                "element": element_name,
                "path": attributes.get("Output Path", ""),
                "output_element": attributes.get("Output Element", ""),
                "attributes": attributes
            })

    return fields

def process_json_field_removal(data, field_path, modification_mode="comment"):
    """
    Remove or comment a specific field in JSON data using dot notation.
    field_path examples: 'data.shipment.items[0].productId', 'controlFileHeader.fileSenderNumber'
    """
    def navigate_and_modify(obj, path_parts, current_path=""):
        if not path_parts:
            return False

        current_key = path_parts[0]
        remaining_parts = path_parts[1:]

        # Handle array notation like items[0]
        if '[' in current_key and ']' in current_key:
            key_name = current_key.split('[')[0]
            try:
                index = int(current_key.split('[')[1].split(']')[0])
            except (ValueError, IndexError):
                return False

            if isinstance(obj, dict) and key_name in obj:
                if isinstance(obj[key_name], list) and len(obj[key_name]) > index:
                    if not remaining_parts:
                        # This is the final target - modify the array element
                        if modification_mode == "remove":
                            obj[key_name].pop(index)
                        elif modification_mode == "comment":
                            # For arrays, we comment the entire element
                            original_value = obj[key_name][index]
                            obj[key_name][index] = f"commented-{original_value}"
                        return True
                    else:
                        return navigate_and_modify(obj[key_name][index], remaining_parts, f"{current_path}.{current_key}")
        else:
            # Regular object property
            if isinstance(obj, dict):
                if not remaining_parts:
                    # This is the final target field
                    if current_key in obj:
                        if modification_mode == "remove":
                            del obj[current_key]
                        elif modification_mode == "comment":
                            obj[f"commented-{current_key}"] = obj.pop(current_key)
                        return True
                else:
                    # Navigate deeper
                    if current_key in obj:
                        return navigate_and_modify(obj[current_key], remaining_parts, f"{current_path}.{current_key}")
            elif isinstance(obj, list):
                # Try to navigate through all items in list
                for item in obj:
                    if navigate_and_modify(item, path_parts, current_path):
                        return True

        return False

    # Clean up path and split
    if not field_path or field_path.strip() == "":
        return False

    # Remove leading/trailing slashes and normalize
    clean_path = field_path.strip().replace('/', '.').strip('.')
    if not clean_path:
        return False

    path_parts = [part for part in clean_path.split('.') if part]
    return navigate_and_modify(data, path_parts)

def process_xml_field_removal(xml_content, field_path, modification_mode="comment"):
    """
    Remove or comment a specific field in XML using XPath-like notation.
    """
    try:
        root = ET.fromstring(xml_content)

        # Find the target element using simplified path matching
        elements = root.findall(f".//{field_path.split('/')[-1]}")

        modified = False
        for element in elements:
            parent = root.find(f".//{element.tag}/..")
            if parent is not None:
                if modification_mode == "remove":
                    parent.remove(element)
                elif modification_mode == "comment":
                    # Create comment node
                    comment_text = f" commented-{element.tag}: {element.text} "
                    parent.insert(list(parent).index(element), ET.Comment(comment_text))
                    parent.remove(element)
                modified = True

        if modified:
            return ET.tostring(root, encoding='unicode')
    except ET.ParseError:
        print(f"❌ XML parsing error for field: {field_path}")

    return xml_content

def process_edi_field_removal(edi_content, field_path, modification_mode="remove"):
    """
    Remove or empty specific fields in EDI format.
    field_path examples: 'ISA01.1', 'N40501', 'ST01'
    """
    lines = edi_content.split('\n')
    modified_lines = []

    for line in lines:
        if not line.strip():
            modified_lines.append(line)
            continue

        # Parse EDI segment
        if '~' in line:
            elements = line.split('*')
            segment_id = elements[0] if elements else ""

            # Check if this line contains our target field
            if field_path.startswith(segment_id):
                # Extract element and subelement numbers
                field_part = field_path[len(segment_id):]
                if field_part.startswith('.'):
                    field_part = field_part[1:]

                try:
                    if '.' in field_part:
                        element_num, subelement_num = field_part.split('.')
                        element_num, subelement_num = int(element_num), int(subelement_num)
                    else:
                        element_num = int(field_part) if field_part.isdigit() else int(field_part[:2])
                        subelement_num = None

                    # Modify the specific element
                    if len(elements) > element_num:
                        if subelement_num is not None:
                            # Handle subelements (composite elements)
                            subelements = elements[element_num].split(':') if ':' in elements[element_num] else [elements[element_num]]
                            if len(subelements) > subelement_num - 1:
                                if modification_mode == "remove":
                                    subelements[subelement_num - 1] = ""
                                elif modification_mode == "comment":
                                    subelements[subelement_num - 1] = f"commented-{subelements[subelement_num - 1]}"
                                elements[element_num] = ':'.join(subelements)
                        else:
                            # Handle simple elements
                            if modification_mode == "remove":
                                elements[element_num] = ""
                            elif modification_mode == "comment":
                                elements[element_num] = f"commented-{elements[element_num]}"

                    line = '*'.join(elements)
                except (ValueError, IndexError):
                    pass  # Skip malformed field paths

        modified_lines.append(line)

    return '\n'.join(modified_lines)

def process_edifact_field_removal(edifact_content, field_path, modification_mode="remove"):
    """
    Remove or empty specific fields in EDIFACT format.
    Similar to EDI but uses + as element separator and : for subelements
    """
    lines = edifact_content.split("'")
    modified_lines = []

    for line in lines:
        if not line.strip():
            modified_lines.append(line)
            continue

        # Parse EDIFACT segment
        if '+' in line:
            elements = line.split('+')
            segment_id = elements[0] if elements else ""

            # Check if this line contains our target field
            if field_path.startswith(segment_id):
                # Extract element number
                field_part = field_path[len(segment_id):]
                if field_part.startswith('.'):
                    field_part = field_part[1:]

                try:
                    element_num = int(field_part) if field_part.isdigit() else int(field_part[:2])

                    # Modify the specific element
                    if len(elements) > element_num:
                        if modification_mode == "remove":
                            elements[element_num] = ""
                        elif modification_mode == "comment":
                            elements[element_num] = f"commented-{elements[element_num]}"

                    line = '+'.join(elements)
                except (ValueError, IndexError):
                    pass  # Skip malformed field paths

        modified_lines.append(line)

    return "'".join(modified_lines)

def process_idoc_field_removal(idoc_content, field_path, modification_mode="remove"):
    """
    Remove or empty specific fields in IDOC format.
    IDOC uses fixed-width fields and segment structures
    """
    lines = idoc_content.split('\n')
    modified_lines = []

    for line in lines:
        # IDOC segments start with E1, E2, etc.
        if line.startswith('E1') or line.startswith('E2'):
            segment_type = line[:6]  # E1EDK01, etc.

            if field_path.startswith(segment_type):
                # For IDOC, we'd need specific field position mappings
                # This is a simplified version - real implementation would need IDOC structure definitions
                if modification_mode == "remove":
                    # Zero out specific field positions
                    line = re.sub(r'(\w+)', lambda m: ' ' * len(m.group(1)), line)
                elif modification_mode == "comment":
                    line = f"* commented: {line}"

        modified_lines.append(line)

    return '\n'.join(modified_lines)

def generate_test_files(test_type="required"):
    """
    Generate test files for missing required or optional fields.
    test_type: 'required' or 'optional'
    """
    print(f"🔧 Loaded Configuration: {CONFIG}")

    # Load spec file to find fields
    with open(CONFIG["spec_file"], "r") as f:
        spec_data = json.load(f)

    # Load max file content
    with open(CONFIG["max_file"], "r") as f:
        max_content = f.read()

    # Detect file format
    file_format = detect_file_format(CONFIG["max_file"])
    print(f"📋 Detected format: {file_format}")

    # Find target fields based on occurrence
    target_occurrence = "1...1" if test_type == "required" else "0...1"
    target_fields = find_fields_by_occurrence(spec_data, target_occurrence)

    print(f"🎯 Found {len(target_fields)} {test_type} fields to process")

    modification_mode = CONFIG.get("modification_mode", "comment")
    output_prefix = CONFIG.get("output_prefix", f"MISS-{test_type.upper()}_")

    # Generate test file for each target field
    for i, field in enumerate(target_fields, 1):
        try:
            # Create a copy of the original content
            if file_format == "JSON":
                data = json.loads(max_content)
                # Build field path from Output Path and Output Element
                field_path = f"{field['path'].replace('/JSON/', '').replace('JSON/', '')}"
                if field['output_element']:
                    field_path = f"{field_path}.{field['output_element']}" if field_path else field['output_element']

                success = process_json_field_removal(data, field_path, modification_mode)
                if success:
                    modified_content = json.dumps(data, indent=2)
                else:
                    print(f"⚠️ Could not modify field: {field_path}")
                    continue

            elif file_format == "XML":
                field_path = field['output_element'] or field['element']
                modified_content = process_xml_field_removal(max_content, field_path, modification_mode)

            elif file_format == "EDI-X12":
                field_path = field['element']
                modified_content = process_edi_field_removal(max_content, field_path, modification_mode)

            elif file_format == "EDIFACT":
                field_path = field['element']
                modified_content = process_edifact_field_removal(max_content, field_path, modification_mode)

            elif file_format == "IDOC":
                field_path = field['element']
                modified_content = process_idoc_field_removal(max_content, field_path, modification_mode)
            else:
                print(f"❌ Unsupported format: {file_format}")
                continue

            # Generate output filename
            safe_field_name = re.sub(r'[^\w\-_]', '_', field['element'])
            output_filename = f"{output_prefix}{safe_field_name}_{i:03d}.{CONFIG['max_file'].split('.')[-1]}"
            output_path = os.path.join(CONFIG["output_directory"], output_filename)

            # Save the modified content
            with open(output_path, "w") as f:
                f.write(modified_content)

            print(f"✅ Generated: {output_filename} (removed {field['element']})")

        except Exception as e:
            print(f"❌ Error processing {field['element']}: {e}")
            continue

    print(f"\n🎉 Generated {len(target_fields)} test files in {CONFIG['output_directory']}")

def main():
    """Main function with user menu or command line args."""
    import sys

    print("=" * 60)
    print("🧪 UNIFIED TEST GENERATOR")
    print("📋 Missing Required/Optional Field Test Creator")
    print("=" * 60)

    # Check for command line arguments
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice == "required" or choice == "1":
            generate_test_files("required")
        elif choice == "optional" or choice == "2":
            generate_test_files("optional")
        elif choice == "both" or choice == "3":
            generate_test_files("required")
            generate_test_files("optional")
        else:
            print(f"❌ Unknown option: {choice}")
            print("Usage: python test_generator.py [required|optional|both]")
        return

    # Interactive mode
    while True:
        print("\n📚 Test Generation Options:")
        print("1️⃣  Generate MISS-RE Tests (Missing Required Fields)")
        print("2️⃣  Generate MISS-OE Tests (Missing Optional Fields)")
        print("3️⃣  Generate Both Test Types")
        print("4️⃣  Exit")
        print("-" * 40)

        try:
            choice = input("🔹 Select option (1-4): ").strip()

            if choice == "1":
                generate_test_files("required")
            elif choice == "2":
                generate_test_files("optional")
            elif choice == "3":
                generate_test_files("required")
                generate_test_files("optional")
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()