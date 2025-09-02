import json
import os

# Load configuration from config.json
# Get the current script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the relative path to config.json
CONFIG_PATH = os.path.join(BASE_DIR, "..", "config", "config.json")

# Load configuration from config.json
with open(CONFIG_PATH, "r") as config_file:
    config_raw = json.load(config_file)

# Convert relative paths to absolute paths from project root
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
CONFIG = config_raw.copy()
CONFIG["spec_file"] = os.path.join(ROOT_DIR, config_raw["spec_file"])
CONFIG["max_file"] = os.path.join(ROOT_DIR, config_raw["max_file"])
CONFIG["output_directory"] = os.path.join(ROOT_DIR, config_raw["output_directory"])

# Debugging: Print the loaded configuration
print("🔧 Loaded Configuration:", CONFIG)

# Ensure output directory exists
os.makedirs(CONFIG["output_directory"], exist_ok=True)

def find_and_modify_keys(data, key_to_find, modification_mode, modified_keys):
    """Recursively searches for key_to_find in a nested dictionary and modifies every occurrence."""

    if isinstance(data, dict):
        if key_to_find in data:
            # Modify the key if found
            if modification_mode == "remove":
                del data[key_to_find]  # ✅ Remove key
                print(f"❌ Removed: {key_to_find}")
            elif modification_mode == "comment":
                data[f"commented-{key_to_find}"] = data.pop(key_to_find)  # ✅ Comment key
                print(f"📝 Commented: {key_to_find}")

            # Add modified key to the list to track changes
            modified_keys.append(key_to_find)

        # Recursively check inside nested dictionaries
        for sub_key in data:
            find_and_modify_keys(data[sub_key], key_to_find, modification_mode, modified_keys)

    elif isinstance(data, list):
        for item in data:
            find_and_modify_keys(item, key_to_find, modification_mode, modified_keys)

def modify_json_and_generate_files():
    """Modifies sampleMax.json based on spec.json conditions and generates separate files for optional fields."""

    # Load spec.json (contains rules)
    with open(CONFIG["spec_file"], "r") as f:
        spec_data = json.load(f)

    # Load sampleMax.json (the full file to be modified)
    with open(CONFIG["max_file"], "r") as f:
        max_data = json.load(f)

    modified_keys = []  # To keep track of modified fields
    found = False  # Flag to check if any modifications were made
    modification_mode = CONFIG["modification_mode"]  # Read from config

    # Iterate through spec.json and find fields with "Source Occurs": "0...1"
    for key, details in spec_data.items():
        if not isinstance(details, dict):
            continue  # Skip if details is not a dictionary

        print(f"Checking key: {key}")

        if details.get("Source Occurs") in ("0...1", "0...*"):
            print(f"✅ Found key '{key}' with 'Source Occurs: 0...1'")

            modified_data = json.loads(json.dumps(max_data))  # Deep copy of max_data

            # Call the modified recursive function to search and modify all occurrences
            find_and_modify_keys(modified_data, key, modification_mode, modified_keys)

            if key in modified_keys:  # Check if the key was modified
                found = True  # Mark that at least one modification was made

                # Generate new filename
                output_file = os.path.join(CONFIG["output_directory"], f"{CONFIG['output_prefix']}MissOE-{key}.json")
                print(f"📂 Generating file: {output_file}")

                # Save modified file
                with open(output_file, "w") as f:
                    json.dump(modified_data, f, indent=4)

            else:
                print(f"⚠️ Key '{key}' not found in sampleMax.json. Skipping modification.")

    if found:
        # Log modified keys
        modified_log_file = os.path.join(CONFIG["output_directory"], "_optional_missing_keys.txt")
        with open(modified_log_file, "w") as log_file:
            log_file.write("\n".join(modified_keys))
        print(f"📝 Modification log saved in: {modified_log_file}")
    else:
        print("⚠️ No modifications were made. Check if the keys actually exist in sampleMax.json.")

# Run function
modify_json_and_generate_files()
