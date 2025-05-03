from flask import Blueprint, request, jsonify
import sys
import os
import datetime

# Add parent directory to path to import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chat import answer_question
from logging_Setup import get_logger

logger= get_logger(__name__)

# Create Blueprint for file processing routes
chat_processing_bp = Blueprint('chatprocess', __name__)

@chat_processing_bp.route('/process', methods=['POST'])
def chat():

    data = request.get_json()
    try:
        if not data or ('inputData' not in data and "workspace" not in data and "questionType" not in data):
            return jsonify({
                    "status": "error",
                    "message": "Missing required parameter",
                    "error_type": "missing_parameter"
                }), 400

        message = data['inputData']
        workspace = data.get('workspace')
        question_type = data.get('questionType')

        # Call the answer_question function from the chat module
        answer = answer_question(message,question_type, workspace)

        return jsonify({"answer": answer}), 200
    except Exception as e:
        logger.error(f"Unexpected Error in chat endpoint: {str(e)}")
        return jsonify({
                "status": "error",
                "message": str(e),
                "error_type": "internal_error"
            }), 500

