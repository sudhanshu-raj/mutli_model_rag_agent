from flask import Blueprint, request, jsonify,send_from_directory
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from logging_Setup import get_logger

logger= get_logger(__name__)

file_access = Blueprint('fileAccess', __name__)
IMAGE_STORAGE_DIR = cfg.IMAGE_STORAGE_DIR
UPLOAD_DIR = cfg.UPLOAD_DIR
OUTPUT_DIR = cfg.OUTPUT_DIR

@file_access.route("/images/<filename>")
def serve_file_from_images(filename):
    return send_from_directory(IMAGE_STORAGE_DIR, filename)

@file_access.route("/files/<workspace>/<filename>")
def serve_file_from_uploadDIR_V1(workspace,filename):
    workspace = request.view_args.get('workspace')
    if not workspace:
        return jsonify({"error": "Workspace not specified"}), 400
    filename=request.view_args.get('filename')
    filePath=os.path.join(UPLOAD_DIR,workspace)
    if not os.path.exists(filePath):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(filePath, filename)

@file_access.route("/files/<path:filePath>")
def serve_file_from_uploadDIR_V2(filePath):
    fullfilePath = os.path.join(UPLOAD_DIR,filePath)
    if not os.path.exists(fullfilePath):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(UPLOAD_DIR, filePath)

@file_access.route("/outputfiles/<path:filePath>")
def serve_file_from_outputDIR_path(filePath):

    fullfilePath = os.path.join(OUTPUT_DIR,filePath)
    if not os.path.exists(fullfilePath):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(OUTPUT_DIR , filePath)

# Now http://your-domain.com/files/myfile.pdf will return the file
