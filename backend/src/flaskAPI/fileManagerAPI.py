from flask import Blueprint, request, jsonify
import sys
import os
from werkzeug.utils import secure_filename

# Add parent directory to path to import FileManager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fileUploadManager import FileManager
import config as cfg
from logging_Setup import get_logger

logger = get_logger(__name__)

# Create Blueprint for file manager routes
file_manager_bp = Blueprint('file_manager', __name__)


print(f"Using upload directory: {cfg.UPLOAD_DIR}")

# Create FileManager instance
file_manager = FileManager()

@file_manager_bp.route('/download', methods=['POST'])
def download_file_api():
    """
    API endpoint to download a file from a URL
    
    Expected JSON payload:
    {
        "url": "https://example.com/file.pdf",
        "max_size_mb": 15  # Optional, defaults to 15
    }
    
    Returns:
        200 OK: File details if download is successful
        400 Bad Request: If URL is missing or invalid
        403 Forbidden: If file type is not allowed
        413 Payload Too Large: If file exceeds size limit
        500 Internal Server Error: For other errors
    """
    try:
        # Get data from request
        data = request.get_json()
        
        if not data or ('url' not in data and "workspace_name" not in data):
            return jsonify({
                "status": "error",
                "error_type": "missing_parameter",
                "message": "Missing URL parameter"
            }), 400
            
        url = data['url']
        workspace_name = data.get('workspace_name', None)
        # max_size_mb = data.get('max_size_mb', 15)
        
        # Download the file
        result = file_manager.download_file_api(url,workspace_name)
        
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            # Map error types to HTTP status codes
            error_status_codes = {
                "file_type_error": 403,
                "file_size_error": 413,
                "download_error": 400,
                "unknown_error": 500
            }
            
            status_code = error_status_codes.get(result.get("error_type", "unknown_error"), 400)
            return jsonify(result), status_code
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": str(e)
        }), 500

# This API can take multiple files in a single request and upload to upload directory
@file_manager_bp.route('/upload', methods=['POST'])
def upload_file_api():
    """
    API endpoint to upload files from frontend
    
    Expected form data:
    - file(s): One or more files to upload
    - workspace_name: (Optional) Name of workspace to store files
    
    Returns:
        200 OK: File details if upload is successful
        400 Bad Request: If no files are provided or other validation fails
        413 Payload Too Large: If file exceeds size limit
        415 Unsupported Media Type: If file type is not allowed
        500 Internal Server Error: For other errors
    """
    try:
        # Log request information
        client_ip = request.remote_addr
        logger.info(f"File upload request received from {client_ip}")
        
        # Check if the request has files
        if 'file' not in request.files:
            logger.warning(f"Upload request from {client_ip} missing 'file' field")
            return jsonify({
                "status": "error",
                "error_type": "missing_file",
                "message": "No files were provided"
            }), 400
            
        # Get workspace name from form data
        workspace_name = request.form.get('workspace_name', None)
        logger.info(f"Upload request for workspace: {workspace_name or 'default'}")
        
        # Handle single file and multiple files
        files = request.files.getlist('file')
        
        if not files or len(files) == 0:
            logger.warning(f"Upload request contained no actual files")
            return jsonify({
                "status": "error",
                "error_type": "missing_file",
                "message": "No files were provided"
            }), 400
        
        logger.info(f"Processing {len(files)} file(s) for upload")
            
        # Process each uploaded file
        results = []
        errors = []
        
        for uploaded_file in files:
            if uploaded_file.filename == '':
                logger.warning("Skipping file with empty filename")
                continue
                
            # Create safe filename
            original_filename = uploaded_file.filename
            filename = secure_filename(uploaded_file.filename)

             # If extension is .webp, replace it with .png
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".webp":
                base_name = os.path.splitext(filename)[0]
                filename = base_name + ".png"
                logger.info(f"Renamed .webp to .png => {filename}")
            
            if original_filename != filename:
                logger.info(f"Sanitized filename from '{original_filename}' to '{filename}'")
            
            # Check file extension
            ext = os.path.splitext(filename)[1].lower()
            if ext not in cfg.ALLWOED_EXTENSIONS:
                logger.warning(f"Rejected file '{filename}' with disallowed type: {ext}")
                errors.append({
                    "filename": filename,
                    "error": f"File type {ext} is not allowed",
                    "error_type": "invalid_file_type"
                })
                continue
                
            # Prepare save location
            if workspace_name:
                save_dir = os.path.join(cfg.UPLOAD_DIR, workspace_name)
                # Create workspace directory if it doesn't exist
                if not os.path.exists(save_dir):
                    logger.info(f"Creating workspace directory: {save_dir}")
                    os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = cfg.UPLOAD_DIR
                
            file_path = os.path.join(save_dir, filename)
            logger.debug(f"Planned save path: {file_path}")
            
            # Check if file already exists
            if os.path.exists(file_path):
                logger.info(f"File already exists: {file_path}")
                file_details = file_manager.get_file_details(file_path)
                results.append({
                    "filename": filename,
                    "path": file_path,
                    "size": file_details["size_bytes"],
                    "size_human": file_details["size_human"],
                    "already_exists": True
                })
                continue
                
            # Save the file
            logger.debug(f"Saving file to {file_path}")
            try:
                uploaded_file.save(file_path)
                logger.info(f"Successfully saved file: {filename}")
            except Exception as save_error:
                logger.error(f"Failed to save file {filename}: {str(save_error)}")
                errors.append({
                    "filename": filename,
                    "error": f"Failed to save file: {str(save_error)}",
                    "error_type": "save_error"
                })
                continue
            
            # Get file details
            file_details = file_manager.get_file_details(file_path)
            
            # Check file size after saving
            if file_details["size_bytes"] > cfg.MAX_FILE_SIZE_BYTES:
                # File is too large, delete it
                logger.warning(f"File too large: {filename} ({file_details['size_human']})")
                os.remove(file_path)
                errors.append({
                    "filename": filename,
                    "error": f"File size exceeds the maximum limit of {cfg.MAX_FILE_SIZE_BYTES/1048576:.1f}MB",
                    "error_type": "file_too_large"
                })
                continue
                
            # File saved successfully
            logger.info(f"File uploaded successfully: {filename} ({file_details['size_human']})")
            results.append({
                "filename": filename,
                "path": file_path,
                "size": file_details["size_bytes"],
                "size_human": file_details["size_human"],
                "already_exists": False,
                "mime_type": file_details["mime_type"]
            })
        
        # Prepare the response
        if len(results) > 0:
            logger.info(f"Upload complete: {len(results)} file(s) successful, {len(errors)} failure(s)")
            return jsonify({
                "status": "success",
                "message": f"Uploaded {len(results)} file(s) successfully",
                "data": {
                    "uploaded_files": results,
                    "errors": errors,
                    "workspace": workspace_name
                }
            }), 200
        elif len(errors) > 0:
            # All files had errors
            logger.error(f"Upload failed: All {len(errors)} file(s) had errors")
            return jsonify({
                "status": "error",
                "error_type": "upload_failed",
                "message": "All file uploads failed",
                "errors": errors
            }), 400
        else:
            # No files processed
            logger.warning("Upload request resulted in no files processed")
            return jsonify({
                "status": "error",
                "error_type": "no_files_processed",
                "message": "No files were processed"
            }), 400
            
    except Exception as e:
        logger.exception(f"Unhandled exception in file upload: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": str(e)
        }), 500



# Add this to your index.py
# from fileManagerAPI import file_manager_bp
# app.register_blueprint(file_manager_bp, url_prefix='/api/files')