#!/usr/bin/env python3
"""
Cloud Run Service - HTTP server for calendar parsing
====================================================
Handles HTTP requests with image uploads and routes to appropriate parser.

Environment Variables:
    USE_LLM: 'true' or 'false' - which parser to use
    GEMINI_API_KEY: Required if USE_LLM=true
    PORT: HTTP server port (default: 8080)

Endpoints:
    POST / - Upload image for parsing
    GET /health - Health check
    GET /info - Service info

Deploy to Cloud Run:
    gcloud run deploy calhero \\
        --source . \\
        --allow-unauthenticated \\
        --set-env-vars USE_LLM=false \\
        --memory 1Gi
"""

import os
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify
import argparse

# Import shared utilities and parsers
from calendar_utils import get_calendar_service, Config, move_to_processed
from calhero_ml import process_image_with_ml


app = Flask(__name__)

# Determine which parser to use
USE_LLM = os.getenv('USE_LLM', 'false').lower() == 'true'

if USE_LLM:
    from google import genai
    from calhero import process_image
    print("🤖 Using LLM Parser (Gemini)")
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
else:
    print("🔍 Using ML/OCR Parser (Tesseract)")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run."""
    return jsonify({
        'status': 'healthy',
        'parser': 'llm' if USE_LLM else 'ml',
        'version': '1.0.0'
    }), 200


@app.route('/info', methods=['GET'])
def service_info():
    """Service information endpoint."""
    return jsonify({
        'service': 'Calendar Parser',
        'parser_type': 'LLM (Gemini)' if USE_LLM else 'ML/OCR (Tesseract)',
        'endpoints': {
            'parse': 'POST /',
            'health': 'GET /health',
            'info': 'GET /info'
        }
    }), 200


@app.route('/', methods=['POST'])
def parse_calendar():
    """
    Main endpoint - accepts image and parses calendar shifts.
    
    Accepts:
        - multipart/form-data with 'image' field
        - application/json with 'image_base64' field
        
    Query params:
        - dry_run: 'true' or 'false' (default: false)
        - check_only: 'true' or 'false' (default: false)
        - force: 'true' or 'false' (default: false)
        - calendar_id: Optional calendar ID to override env var
        
    Returns:
        JSON with parsing results
    """
    try:
        # Parse request
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload
            file = request.files.get('image')
            if not file:
                return jsonify({'error': 'No image provided'}), 400
            
            image_data = file.read()
            image_name = file.filename or 'schedule.png'
        
        elif request.content_type == 'application/json':
            # JSON with base64
            import base64
            data = request.get_json()
            
            if 'image_base64' not in data:
                return jsonify({'error': 'No image_base64 field in JSON'}), 400
            
            image_data = base64.b64decode(data['image_base64'])
            image_name = data.get('image_name', 'schedule.png')
        
        else:
            return jsonify({
                'error': 'Unsupported content type',
                'supported': ['multipart/form-data', 'application/json']
            }), 400
        
        # Save image temporarily
        suffix = Path(image_name).suffix or '.png'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(image_data)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Parse arguments
            class Args:
                dry_run = request.args.get('dry_run', 'false').lower() == 'true'
                check_only = request.args.get('check_only', 'false').lower() == 'true'
                force = request.args.get('force', 'false').lower() == 'true'
                debug = request.args.get('debug', 'false').lower() == 'true'
            
            args = Args()
            
            # Validate flag combinations
            if args.dry_run and args.check_only:
                return jsonify({
                    'success': False,
                    'error': 'Cannot use dry_run and check_only together'
                }), 400
            
            # Get active calendar ID if needed
            if args.dry_run:
                calendar_id = None
                service = None
                mode = "dry-run"
            else:
                calendar_id_override = request.args.get('calendar_id')
                try:
                    calendar_id, source = Config.get_active_calendar_id(calendar_id_override)
                    print(f"📅 Using calendar from {source}")
                except ValueError as e:
                    return jsonify({
                        'success': False,
                        'error': f'Configuration error: {str(e)}'
                    }), 400
                service = get_calendar_service()
                mode = "check-only" if args.check_only else "normal"
            
            # Process image with selected parser
            if USE_LLM:
                created_count, would_create = process_image(service, client, tmp_path, args, calendar_id)
                parser_used = 'LLM (Gemini)'
            else:
                created_count, would_create = process_image_with_ml(service, tmp_path, args, calendar_id)
                parser_used = 'ML/OCR (Tesseract)'
            
            # Success response
            response_data = {
                'success': True,
                'parser': parser_used,
                'image_name': image_name,
                'mode': mode
            }
            
            if args.dry_run or args.check_only:
                response_data['would_create'] = would_create
            else:
                response_data['shifts_created'] = created_count
                response_data['calendar_source'] = source
            
            return jsonify(response_data), 200
        
        finally:
            # Cleanup temp file
            if tmp_path.exists():
                tmp_path.unlink()
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    # Get port from environment (Cloud Run provides PORT)
    port = int(os.getenv('PORT', 8080))
    
    print(f"🚀 Starting Calendar Parser Service on port {port}")
    print(f"   Parser: {'LLM (Gemini)' if USE_LLM else 'ML/OCR (Tesseract)'}")
    
    # Run server
    app.run(host='0.0.0.0', port=port, debug=False)
