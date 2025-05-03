import json
import os
from datetime import datetime
import config as cfg

JSON_FILE = cfg.ALL_FILES_LIST  # JSON file path
DOCS_METADATA_FILE=cfg.DOCS_METADATA_FILE

def load_json():
    """Load existing JSON data from file or return an empty list if file doesn't exist."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # Return empty list if JSON is corrupted
    return []


def save_json(data):
    """Save updated JSON data to file."""
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def extract_filename(file_path):
    """Extracts the filename from the given file path."""
    return os.path.basename(file_path)


def file_exists(json_data, file_path,workspace_name):
    """Check if a file (based on filename) already exists in the JSON data."""
    file_name = extract_filename(file_path)
    return any(
        extract_filename(entry["file_path"]) == file_name and 
        entry.get("workspace_name", "").lower() == (workspace_name or "").lower()
        for entry in json_data
)


def add_file_to_json(file_path, doc_type,workspace_name):
    """Add a new file entry to the JSON data if it doesn't already exist."""
    json_data = load_json()

    if file_exists(json_data, file_path,workspace_name):
        print(
            f"File '{extract_filename(file_path)}' already exists in the JSON data.")
        return False

    new_entry = {
        "file_path": file_path,
        "doc_type": doc_type,
        "added_at": datetime.utcnow().isoformat() , # Adding timestamp in ISO format
        "workspace_name":workspace_name
    }

    json_data.append(new_entry)
    save_json(json_data)
    # print(f"File '{extract_filename(file_path)}' added successfully.")
    return True

def _update_DOCX_metadata_file(doc_id, metadata):
        """Update the central metadata JSON file"""
        try:
            # Initialize empty data if file doesn't exist
            if not os.path.exists(DOCS_METADATA_FILE):
                data = {}
            else:
                # Handle empty file case
                if os.path.getsize(DOCS_METADATA_FILE) == 0:
                    data = {}
                else:
                    with open(DOCS_METADATA_FILE, "r") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            print("Corrupted metadata file, resetting...")
                            data = {}

            data[doc_id] = metadata

            with open(DOCS_METADATA_FILE, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Metadata update failed: {str(e)}")
            # Create empty file as fallback
            with open(DOCS_METADATA_FILE, "w") as f:
                json.dump({}, f)

def remove_file_from_json(file_path):
    """
    Remove a file entry from the JSON data.
    
    Args:
        file_path (str): Path of the file to remove
        
    Returns:
        bool: True if file was found and removed, False otherwise
    """
    json_data = load_json()
    file_name = extract_filename(file_path)
    
    # Find all matching entries (there might be multiple entries with the same filename)
    matching_entries = [
        i for i, entry in enumerate(json_data) 
        if extract_filename(entry["file_path"]) == file_name
    ]
    
    if not matching_entries:
        print(f"File '{file_name}' not found in the JSON data.")
        return False
    
    # Remove all matching entries (in reverse order to avoid index shifting problems)
    for index in sorted(matching_entries, reverse=True):
        removed_entry = json_data.pop(index)
        print(f"Removed entry: {removed_entry['file_path']}")
    
    # Save updated data
    save_json(json_data)
    
    # Also remove from metadata file if it exists as it is not required now
    # try:
    #     if os.path.exists(DOCS_METADATA_FILE):
    #         with open(DOCS_METADATA_FILE, "r") as f:
    #             metadata = json.load(f)
            
    #         # Check if the file exists in metadata (using filename as key)
    #         removed_metadata = False
    #         keys_to_remove = []
            
    #         for key, value in metadata.items():
    #             # Check if this metadata entry references our file
    #             if key == file_name or (
    #                 isinstance(value, dict) and 
    #                 value.get("source") and 
    #                 extract_filename(value["source"]) == file_name
    #             ):
    #                 keys_to_remove.append(key)
    #                 removed_metadata = True
            
    #         # Remove matching metadata entries
    #         for key in keys_to_remove:
    #             del metadata[key]
                
    #         # Save updated metadata
    #         if removed_metadata:
    #             with open(DOCS_METADATA_FILE, "w") as f:
    #                 json.dump(metadata, f, indent=2)
    #             print(f"Removed metadata for '{file_name}'")
    # except Exception as e:
    #     print(f"Error removing metadata: {str(e)}")
    
    return True
