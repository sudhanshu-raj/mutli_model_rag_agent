import os
import datetime
import util
from logging_Setup import get_logger
import json_functions as JC
import config as cfg

max_size_mb = cfg.MAX_FILE_SIZE_MB

logger=get_logger(__name__)

def list_files_in_folder(folder_path):
    # Change this to your folder path
    # List all files in the folder
    files = [os.path.join(folder_path, f) for f in os.listdir(
        folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    return files


def is_file_too_large(file_path, max_size_mb=15):
    """
    Check if a file exceeds specified size limit in megabytes.

    Args:
        file_path (str): Path to the file
        max_size_mb (int): Maximum allowed size in megabytes (default: 6)

    Returns:
        bool: True if file exceeds limit, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    # Convert MB to bytes
    max_size_bytes = max_size_mb * 1024 * 1024
    file_size = os.path.getsize(file_path)

    if file_size > max_size_bytes:
        print(
            f"File size {file_size/1024/1024:.2f}MB exceeds {max_size_mb}MB limit")
        return True
    return False


def save_text_to_file(text, directory):
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Generate filename with current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.txt"
    filepath = os.path.join(directory, filename)

    # Write text to file
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(text)

    return filepath

def revert_fileAdded(file_path):
    # Cleanup code...
        file_name = os.path.basename(file_path)
        output_path = f"media/output/{file_name}"
        base_dir=cfg.BASE_DIR
        output_path = os.path.join(base_dir, output_path)
        
        # Check if the output directory exists and remove it
        util.remove_files(output_path)
       
        # Also remove from all_files_list metadata records
        try:
            JC.remove_file_from_json(file_path)
            logger.info(f"Removed file from metadata records: {file_path}")
        except Exception as record_error:
            logger.error(f"Error removing metadata records: {record_error}")

if __name__ == "__main__":
    text = '''
    # filepaths for multi agent modal testing
file_paths = [
    "C:\\Users\\rajsu\\Downloads\\Iphoneinvoicev2.pdf",
    "C:\\Users\\rajsu\\Downloads\\my_resume.pdf",
    "C:\\Users\\rajsu\\Downloads\\candidate1_resume.pdf",
    "C:\\Users\\rajsu\\Downloads\\candidate2_resume.pdf",
    "C:\\Users\\rajsu\\Downloads\\Railwire_Subscriber_Invoice.pdf",
    "C:\\Users\\rajsu\\Downloads\\invoice_19531402117.pdf",
    "C:\\Users\\rajsu\\Downloads\\Satyendra Rai - Resume - Software Engineer.txt",
    "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\all_in_one.txt",
    "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\gamingCredentials.txt",
    "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\mysql.txt",
    "C:\\Users\\rajsu\\OneDrive\\Documents\\myCredentials\\steam credentials.txt",
    "C:\\Users\\rajsu\\OneDrive\\Documents\\amity_projects_sem4\\admit_Card.pdf",
    "C:\\Users\\rajsu\\Downloads\\cp_plus_manual.pdf",
    "C:\\Users\\rajsu\\Downloads\\legion_5_5i_15_9_ug_en.pdf"
]

# Command to start the fastapi server :
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

    '''
    file_path = save_text_to_file(text, "uploaded_files")
    print(file_path)
