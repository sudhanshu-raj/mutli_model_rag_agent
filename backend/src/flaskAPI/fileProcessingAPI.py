from flask import Blueprint, request, jsonify
import sys
import os
import datetime

# Add parent directory to path to import process_files_api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from process_files import process_files_api, generate_image_description

# Create Blueprint for file processing routes
file_processing_bp = Blueprint('file_processing', __name__)

@file_processing_bp.route('/process', methods=['POST'])
def process_file_api_route():
    try:
        data = request.get_json()
        
        if not data or ('file_path' not in data and "workspace_name" not in data):
            return jsonify({
                "status": "error",
                "message": "Missing file_path parameter",
                "error_type": "missing_parameter"
            }), 400
            
        file_path = data['file_path']
        image_metadata = data.get('image_metadata', {})
        workspace_name = data.get('workspace_name', None)
        
        # Process file and get response
        result = process_files_api(file_path, image_metadata, workspace_name)
        
        # Return appropriate status code based on response
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            # Map error types to status codes
            error_status_codes = {
                "file_already_exists": 409,  # Conflict
                "file_too_large": 413,       # Payload Too Large
                "invalid_file_type": 415,    # Unsupported Media Type
                "file_not_found": 404,       # Not Found
                "processing_failed": 422,    # Unprocessable Entity
                "unexpected_error": 500      # Internal Server Error
            }
            
            status_code = error_status_codes.get(result.get("error_type"), 400)
            return jsonify(result), status_code
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": "server_error"
        }), 500
    

@file_processing_bp.route('/generate_image_description', methods=['GET'])
def generate_image_description_api():
    try:
        if "image_path" not in request.args:
            return jsonify({
                "status": "error",
                "message": "Missing image_path parameter",
                "error_type": "missing_parameter"
            }), 400
        
        image_path = request.args.get("image_path")
        
        # Call the function to generate image title and description
        result = generate_image_description(image_path)

        if result :            
            return jsonify({
                "status": "success",
                "data": result
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to generate image description",
                "error_type": "processing_failed"
            }), 422
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": "server_error"
        }), 500