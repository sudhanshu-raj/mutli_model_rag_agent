import json
from flask import Flask, request, jsonify
from fileManagerAPI import file_manager_bp
from fileProcessingAPI import file_processing_bp
from workspaceManagerAPI import workspace_bp
from chatAPI import chat_processing_bp
from fileAccess import file_access
from flask_cors import CORS
from auth import auth_bp    
import os
import sys
from dotenv import load_dotenv
load_dotenv()


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from logging_Setup import get_logger

logger= get_logger(__name__)

log_file_dir=cfg.LOGS_FILE

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Enable CORS for all routes
# At the top of your file, update CORS to handle error responses

logger.info(f"Allowed origins: {cfg.FRONTEND_ORIGINS}")

CORS(app, 
     resources={r"/*": {
         "origins":cfg.FRONTEND_ORIGINS,
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "X-Secret-Key", "Authorization", "secret_key"],
         "expose_headers": ["Content-Type", "X-Secret-Key", "Authorization"]
     }},
     supports_credentials=True,
     intercept_exceptions=True) 

# Register the blueprints
app.register_blueprint(file_manager_bp, url_prefix='/files')
app.register_blueprint(file_processing_bp, url_prefix='/process_file')
app.register_blueprint(workspace_bp, url_prefix='/workspaces')
app.register_blueprint(chat_processing_bp, url_prefix='/chat')
app.register_blueprint(file_access, url_prefix='/fileAccess')
app.register_blueprint(auth_bp, url_prefix='/auth')

PASSWORD = os.environ["ADMIN_PASSWORD"]
EXCLUDE_PATHS = ['/health','/auth/validate', '/fileAccess/' ]

@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    response = jsonify({"error": "Internal server error", "details": str(e)})
    response.status_code = 500
    return response


@app.before_request
def global_basic_auth():
    # Get the origin from the request
    origin = request.headers.get('Origin')
    
    # Handle None origin safely
    if origin is None:
        allowed_origin = cfg.FRONTEND_ORIGINS[0] if isinstance(cfg.FRONTEND_ORIGINS, list) else cfg.FRONTEND_ORIGINS
    else:
        if isinstance(cfg.FRONTEND_ORIGINS, list):
            allowed_origin = origin if origin in cfg.FRONTEND_ORIGINS else cfg.FRONTEND_ORIGINS[0]
        else:
            allowed_origin = origin if origin == cfg.FRONTEND_ORIGINS else cfg.FRONTEND_ORIGINS
    
    # IMPORTANT: Handle OPTIONS requests first
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', allowed_origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-Secret-Key, Authorization, secret_key')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 200
    
    # Check if path should be excluded from authentication
    should_exclude = False
    for path in EXCLUDE_PATHS:
        if request.path.startswith(path):
            should_exclude = True
            break
            
    # Skip auth for excluded paths
    if should_exclude:
        return None
        
    # Regular auth logic for non-excluded paths
    secret_key = request.headers.get('X-Secret-Key')
    if not secret_key:
        response = jsonify({"error": "Missing secret key header"})
        response.status_code = 401
        response.headers.add('Access-Control-Allow-Origin', allowed_origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    if secret_key != PASSWORD:
        response = jsonify({"error": "Invalid secret key"})
        response.status_code = 401
        response.headers.add('Access-Control-Allow-Origin', allowed_origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Service is running"}), 200

@app.route('/logs', methods=['POST'])
def store_logs():
    print("/logs endpoint called")
    logs = request.json.get('logs', [])
    
    for log in logs:
        # Store in database or log file
        timestamp = log.get('timestamp')
        level = log.get('level')
        message = log.get('message')
        data = log.get('data')
        user_id = log.get('user_id')
        
        # Example: Write to log file
        frontendlog_file=os.path.join(log_file_dir, 'frontend_application.log')
        with open(frontendlog_file, 'a') as log_file:
            log_file.write(f"{timestamp} [{level}] {user_id}: {message}\n")
            if data:
                log_file.write(f"  Data: {json.dumps(data)}\n")
    
    return jsonify({"success": True})

@app.route("/secureapi",methods=["GET"])
def secure_api():
    # This is a secure API endpoint that requires authentication
    return jsonify({"message": "This is a secure API endpoint."})
    
    
def shutdown_handler(signal, frame):
    app.logger.info("Received shutdown signal, exiting gracefully...")
    sys.exit(0)

import signal
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)