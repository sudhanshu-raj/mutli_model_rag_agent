import os
from dotenv import load_dotenv
load_dotenv()

# Get the base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_URL=os.environ.get("BASE_URL","http://localhost/api/") # Update this to your actual base URL

# Define paths using absolute references
IMAGES_METADATA_FILE = os.path.join(BASE_DIR, "media", "files-metadata", "images_metadata.json")
IMAGE_STORAGE_DIR = os.path.join(BASE_DIR, "media", "images")
CHROMA_DATA_DIR = os.path.join(BASE_DIR, "media", "chroma-data")
ALL_FILES_LIST = os.path.join(BASE_DIR, "media", "all_files_list.json")
DOCS_METADATA_FILE = os.path.join(BASE_DIR, "media", "files-metadata", "docs_metadata.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "media", "output")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files")
MAX_FILE_SIZE_MB=15
MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024  # 15 MB in bytes
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 15 MB in bytes
ALLWOED_EXTENSIONS = [".docx", ".doc", ".pdf", ".txt", ".json", ".jpg", ".png", ".jpeg", ".md",".webp"]
ALLWOED_IMAGE_EXTENSIONS=[".png",".jpg","jpeg"]  # here not putting .webp because .webp will converted to .png in end for process
LOGS_FILE=os.path.join(BASE_DIR, "logs")

FRONTEND_ORIGINS=os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173")  # Default to localhost if not set