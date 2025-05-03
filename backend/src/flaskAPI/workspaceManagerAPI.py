from flask import Blueprint, request, jsonify,g
import sys
import os
import datetime
from werkzeug.utils import secure_filename

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database
from logging_Setup import get_logger
import config as cfg
from delete_document import delete_file_api,delete_workspace_api

# Setup logger
logger = get_logger(__name__)

# Create Blueprint for workspace management routes
workspace_bp = Blueprint('workspace_manager', __name__)


@workspace_bp.before_request
def before_request():
    g.db = Database()

@workspace_bp.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db:
        db.conn.close()

@workspace_bp.route('/', methods=['GET'])
def get_all_workspaces():
    """Get list of all workspaces"""
    try:
        # Use the database method instead of direct SQL
        workspaces = g.db.get_all_workspaces()
        
        if workspaces is None:
            logger.error("Database error while retrieving workspaces")
            return jsonify({
                "status": "error",
                "error_type": "database_error",
                "message": "Failed to retrieve workspaces"
            }), 500
        
        logger.info(f"Retrieved {len(workspaces)} workspaces")
        
        return jsonify({
            "status": "success",
            "message": f"Retrieved {len(workspaces)} workspaces",
            "data": workspaces
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving workspaces: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Failed to retrieve workspaces: {str(e)}"
        }), 500

@workspace_bp.route('/<workspace_name>', methods=['GET'])
def get_workspace(workspace_name):
    """Get details for a specific workspace"""
    try:
        # Use the database method instead of direct SQL
        workspace = g.db.get_workspace_details(workspace_name)
        
        if workspace is None:
            logger.warning(f"Workspace not found: {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "not_found",
                "message": f"Workspace '{workspace_name}' not found"
            }), 404
        
        logger.info(f"Retrieved workspace: {workspace_name}")
        
        return jsonify({
            "status": "success",
            "message": f"Retrieved workspace details",
            "data": workspace
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving workspace {workspace_name}: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Failed to retrieve workspace: {str(e)}"
        }), 500

@workspace_bp.route('/', methods=['POST'])
def create_workspace():
    """Create a new workspace"""
    try:
        # Get data from request
        data = request.get_json()
        
        if not data or 'workspace_name' not in data:
            logger.warning("Missing workspace_name in request")
            return jsonify({
                "status": "error",
                "error_type": "missing_parameter",
                "message": "Missing workspace_name parameter"
            }), 400
        
        workspace_name = data['workspace_name']
        user_id = data.get('user_id', 'default_user')
        
        # Check if workspace already exists using database method
        existing = g.db.get_workspace_by_name(workspace_name)
        if existing:
            logger.info(f"Workspace already exists: {workspace_name}")
            
            # Get workspace details using database method
            workspace = g.db.get_workspace_details(workspace_name)
            
            return jsonify({
                "status": "success",
                "message": f"Workspace '{workspace_name}' already exists",
                "data": workspace,
                "already_exists": True
            }), 200
        
        # Create workspace directory
        workspace_dir = os.path.join(cfg.UPLOAD_DIR, workspace_name)
        if not os.path.exists(workspace_dir):
            os.makedirs(workspace_dir, exist_ok=True)
            logger.info(f"Created workspace directory: {workspace_dir}")
        
        # Create workspace in database
        workspace_id = g.db.create_workspace(user_id, workspace_name)
        
        if not workspace_id:
            logger.error(f"Failed to create workspace: {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "database_error",
                "message": "Failed to create workspace in database"
            }), 500
        
        logger.info(f"Created workspace: {workspace_name} (ID: {workspace_id})")
        
        # Get complete workspace details using database method
        workspace = g.db.get_workspace_details(workspace_name)
        
        return jsonify({
            "status": "success",
            "message": f"Created workspace '{workspace_name}'",
            "data": workspace,
            "already_exists": False
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating workspace: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Failed to create workspace: {str(e)}"
        }), 500

@workspace_bp.route('/<workspace_name>/files', methods=['GET'])
def get_workspace_files(workspace_name):
    """Get files in a workspace"""
    try:
        # Check if workspace exists using database method
        workspace = g.db.get_workspace_by_name(workspace_name)
        if not workspace:
            logger.warning(f"Workspace not found: {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "not_found",
                "message": f"Workspace '{workspace_name}' not found"
            }), 404
        
        workspace_id = workspace['id']  # First item is the ID
        
        # Get workspace files using database method
        files = g.db.get_workspace_files_detailed(workspace_id)
        
        logger.info(f"Retrieved {len(files) if files else 0} files from workspace '{workspace_name}'")
        
        return jsonify({
            "status": "success",
            "message": f"Retrieved {len(files) if files else 0} files",
            "data": {
                "workspace": workspace_name,
                "files": files or []
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving files for workspace {workspace_name}: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Failed to retrieve files: {str(e)}"
        }), 500

@workspace_bp.route('/<workspace_name>/files', methods=['POST'])
def add_file_to_workspace_api(workspace_name):
    """Add a file entry to a workspace database (without file handling)"""
    try:
        workspace_name = request.view_args['workspace_name']
        
        # Get JSON data
        data = request.get_json()
        if not data or 'file_name' not in data:
            logger.warning(f"Missing file_name in request to workspace '{workspace_name}'")
            return jsonify({
                "status": "error",
                "error_type": "missing_parameter",
                "message": "Missing file_name parameter"
            }), 400
            
        file_name = data['file_name']
        
        # Check if workspace exists
        workspace = g.db.get_workspace_by_name(workspace_name)
        if not workspace:
            logger.warning(f"Workspace not found: {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "not_found",
                "message": f"Workspace '{workspace_name}' not found"
            }), 404
        
        workspace_id = workspace['id']
        
        # Check if file already exists in database
        file_exists, existing_file_id = g.db.check_file_exists_in_workspace(workspace_id, file_name)
        if file_exists:
            logger.info(f"File already exists in workspace: {file_name}")
            return jsonify({
                "status": "success",
                "message": f"File already exists in workspace",
                "data": {
                    "file_name": file_name,
                    "already_exists": True,
                    "file_id": existing_file_id
                }
            }), 200
        
        # Add file entry to database
        file_path = os.path.join(workspace_name, file_name)
        file_id = g.db.add_file_to_workspace(workspace_id, file_name, file_path)
        
        if not file_id:
            logger.error(f"Failed to add file to database: {file_name}")
            return jsonify({
                "status": "error",
                "error_type": "database_error",
                "message": "Failed to add file to database"
            }), 500
        
        logger.info(f"Added file to workspace database: {file_name} (ID: {file_id})")
        
        return jsonify({
            "status": "success",
            "message": f"Added file to workspace '{workspace_name}'",
            "data": {
                "file_id": file_id,
                "file_name": file_name,
                "workspace_name": workspace_name
            }
        }), 201
        
    except Exception as e:
        logger.exception(f"Error adding file to workspace {workspace_name}: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": str(e)
        }), 500

@workspace_bp.route('/<workspace_name>', methods=['DELETE'])
def delete_workspace(workspace_name):
    """Delete a workspace and all its files"""
    try:
        workspace_name = request.view_args['workspace_name']
        if not workspace_name:
            logger.warning(f"Missing workspace_name in request")
            return jsonify({
                "status": "error",
                "error_type": "missing_parameter",
                "message": "Missing workspace_name parameter"
            }), 400
        
        workspace_details=g.db.get_workspace_by_name(workspace_name)
        if not workspace_details:
            logger.warning(f"Workspace not found: {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "not_found",
                "message": f"Workspace '{workspace_name}' not found"
            }), 404
        workspace_info={
            "id":workspace_details["id"],
            "workspace_name":workspace_details["workspace_name"],
        }
        delete_success=delete_workspace_api(workspace_info)
        if not delete_success:
            logger.error(f"Failed to delete workspace: {workspace_name}")
            return jsonify({
                "status": "error",
                "message": "Failed to delete workspace"
            }), 500
        
        logger.info(f"Deleted workspace: {workspace_name}")
        return jsonify({
            "status": "success",
            "message": f"Deleted workspace '{workspace_name}'"
        }), 200

    except Exception as e:
        logger.error(f"Error deleting workspace {workspace_name}: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Failed to delete workspace: {str(e)}"
        }), 500

        
#not used anywhere , have to  check before deleteing this method
# This deletes the file row  from database and also from the upload directory
@workspace_bp.route('/<workspace_name>/<file_id>', methods=['DELETE'])
def delete_workspace_file(workspace_name, file_id):
    """Delete a specific file from a workspace"""
    try:
        # Check if workspace exists
        workspace = g.db.get_workspace_by_name(workspace_name)
        if not workspace:
            logger.warning(f"Workspace not found: {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "not_found",
                "message": f"Workspace '{workspace_name}' not found"
            }), 404
        
        workspace_id = workspace['id']
        
        # Get file details to find the file path
        file_info = g.db.get_file_details(file_id)
        if not file_info:
            logger.warning(f"File not found: ID {file_id} in workspace {workspace_name}")
            return jsonify({
                "status": "error",
                "error_type": "not_found",
                "message": f"File ID {file_id} not found in workspace"
            }), 404
        
        # Delete file from database
        delete_success = g.db.delete_workspace_file(file_id)
        if not delete_success:
            logger.error(f"Database error deleting file ID {file_id}")
            return jsonify({
                "status": "error",
                "error_type": "database_error",
                "message": "Failed to delete file from database"
            }), 500
        
        # Delete the physical file from disk
        file_path = os.path.join(cfg.UPLOAD_DIR, workspace_name, file_info['file_name'])
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        
        return jsonify({
            "status": "success",
            "message": f"Deleted file from workspace '{workspace_name}'",
            "data": {
                "file_id": file_id,
                "file_name": file_info['file_name']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting file {file_id} from workspace {workspace_name}: {str(e)}")
        return jsonify({
            "status": "error",
            "error_type": "server_error",
            "message": f"Failed to delete file: {str(e)}"
        }), 500

@workspace_bp.route('/<workspace_name>/<int:file_id>/doc_ids', methods=['POST'])
def add_doc_id_to_workspace_file(workspace_name, file_id):
    """
    Add a doc_id to the workspace_files_docID table.
    Expects JSON: {"doc_id": "some value"}
    """
    try:
        data = request.get_json()
        if not data or 'doc_id' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing doc_id in JSON body."
            }), 400
        
        # Check if workspace exists
        workspace = g.db.get_workspace_by_name(workspace_name)
        if not workspace:
            return jsonify({
                "status": "error",
                "message": f"Workspace '{workspace_name}' not found."
            }), 404
        
        # Check if file exists
        file_info = g.db.get_file_details(file_id)
        if not file_info:
            return jsonify({
                "status": "error",
                "message": f"File ID {file_id} not found in workspace '{workspace_name}'."
            }), 404
        
        row_id = g.db.add_workspace_file_docID(workspace["id"], file_id, data["doc_id"])
        
        return jsonify({
            "status": "success",
            "message": f"Added doc_id to file {file_id}.",
            "data": {
                "row_id": row_id,
                "doc_id": data["doc_id"]
            }
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@workspace_bp.route('/<workspace_name>/<int:file_id>/doc_ids', methods=['GET'])
def get_doc_ids_for_workspace_file(workspace_name, file_id):
    """
    Get doc IDs for a workspace and file.
    """
    try:
        # Check if workspace exists
        workspace = g.db.get_workspace_by_name(workspace_name)
        if not workspace:
            return jsonify({
                "status": "error",
                "message": f"Workspace '{workspace_name}' not found."
            }), 404
        
        # Check if file exists
        file_info = g.db.get_file_details(file_id)
        if not file_info:
            return jsonify({
                "status": "error",
                "message": f"File ID {file_id} not found in workspace '{workspace_name}'."
            }), 404
        
        doc_ids = g.db.get_workspace_file_docIDs(workspace_id=workspace["id"], file_id=file_id)
        
        return jsonify({
            "status": "success",
            "data": doc_ids
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@workspace_bp.route('/delete/doc_ids', methods=['DELETE'])
def delete_files_from_workspace():

    try:
        data = request.get_json()
        if not data or 'workspaceInfo' not in data or "fileInfo" not in data:
            return jsonify({
                "status": "error",
                "message": "Missing workspaceInfo or fileInfo in JSON body."
            }), 400
        logger.info(f"Received data for deletion: {data}")
        # Map camelCase to snake_case internally
        workspace_info = {
            "id": data['workspaceInfo']['id'],
            "workspace_name": data['workspaceInfo']['workspace_name']
        }
        
        file_info = {
            "id": data['fileInfo']['id'],
            "file_name": data['fileInfo']['file_name']
        }
        logger.info(f"Workspace Info: {workspace_info}")
        logger.info(f"File Info: {file_info}")
        
        # Check if there are doc_ids associated with this file
        doc_ids = g.db.get_workspace_file_docIDs(workspace_id=workspace_info["id"], file_id=file_info["id"])
        if not doc_ids:
            return jsonify({
                "status": "error",
                "message": "No document IDs found for this file."
            }), 404
        
        # Call the delete function
        delete_success = delete_file_api(workspace_info, file_info)
        if not delete_success:
            return jsonify({
                "status": "error",
                "message": "Failed to delete file from database."
            }), 500
        
        return jsonify({
            "status": "success",
            "message": f"Deleted file {file_info['file_name']} from workspace '{workspace_info['workspace_name']}'."
        }), 200
    
    except Exception as e:
        logger.error(f"Error in delete_files_from_workspace: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500