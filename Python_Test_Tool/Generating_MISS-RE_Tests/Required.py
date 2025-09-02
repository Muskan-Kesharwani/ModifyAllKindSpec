import json
import os

# Load configuration from config.json
# Get the current script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the relative path to config.json
CONFIG_PATH = os.path.join(BASE_DIR, "..", "config", "config.json")

# Load configuration from config.json
with open(CONFIG_PATH, "r") as config_file:
    CONFIG = json.load(config_file)

# Debugging: Print the loaded configuration
print("🔧 Loaded Configuration:", CONFIG)

# Ensure output directory exists
os.makedirs(CONFIG["output_directory"], exist_ok=True)


def find_and_modify_keys(data, key_to_find, modification_mode):
    """Recursively searches for key_to_find in a nested dictionary and modifies it."""

    if isinstance(data, dict):
        if key_to_find in data:
            if modification_mode == "remove":
                del data[key_to_find]  # ✅ Remove key
                print(f"❌ Removed: {key_to_find}")
            elif modification_mode == "comment":
                data[f"commented-{key_to_find}"] = data.pop(key_to_find)  # ✅ Comment key
                print(f"📝 Commented: {key_to_find}")
            return True  # Indicate modification happened

        # Recursively check inside nested dictionaries
        for sub_key in data:
            if find_and_modify_keys(data[sub_key], key_to_find, modification_mode):
                return True

    elif isinstance(data, list):
        for item in data:
            if find_and_modify_keys(item, key_to_find, modification_mode):
                return True
    return False


def modify_json_and_generate_files():
    """Modifies sampleMax.json based on spec.json conditions and generates separate files."""

    # Load spec.json (contains rules)
    with open(CONFIG["spec_file"], "r") as f:
        spec_data = json.load(f)

    # Load sampleMax.json (the full file to be modified)
    with open(CONFIG["max_file"], "r") as f:
        max_data = json.load(f)

    modified_keys = []  # To keep track of modified fields
    found = False  # Flag to check if any modifications were made
    modification_mode = CONFIG["modification_mode"]  # Read from config

    # Iterate through spec.json and find fields with "Source Occurs": "1...1"
    for key, details in spec_data.items():
        if not isinstance(details, dict):
            continue  # Skip if details is not a dictionary

        print(f"Checking key: {key}")

        if details.get("Source Occurs") in ("1...1", "1...*"):
            print(f"✅ Found key '{key}' with 'Source Occurs: 1...1'")

            modified_data = json.loads(json.dumps(max_data))  # Deep copy

            if find_and_modify_keys(modified_data, key, modification_mode):
                modified_keys.append(key)  # Store modified key name
                found = True  # Mark that at least one file was modified

                # Generate new filename
                output_file = os.path.join(CONFIG["output_directory"], f"{CONFIG['output_prefix']}MissRE-{key}.json")
                print(f"📂 Generating file: {output_file}")

                # Save modified file
                with open(output_file, "w") as f:
                    json.dump(modified_data, f, indent=4)

            else:
                print(f"⚠️ Key '{key}' not found in sampleMax.json. Skipping modification.")

    if found:
        # Log modified keys
        modified_log_file = os.path.join(CONFIG["output_directory"], "_modified_keys.txt")
        with open(modified_log_file, "w") as log_file:
            log_file.write("\n".join(modified_keys))
        print(f"📝 Modification log saved in: {modified_log_file}")
    else:
        print("⚠️ No modifications were made. Check if the keys actually exist in sampleMax.json.")


# Run function
modify_json_and_generate_files()
