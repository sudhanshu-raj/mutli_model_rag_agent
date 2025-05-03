from flask import Blueprint, request, jsonify
from functools import wraps
import os
from dotenv import load_dotenv
load_dotenv()

auth_bp = Blueprint('auth', __name__)

# Set your password here - ideally should be in config or env var
PASSWORD = os.environ["ADMIN_PASSWORD"]

@auth_bp.route('/validate', methods=['POST'])
def validate_password():
    password = request.json.get('secret_key')
    
    if password == PASSWORD:
        return jsonify({"status": "success", "message": "Authentication successful"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid password"}), 401