import os
import sys
import logging
from datetime import datetime
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from chat import chat_bp
from chat_history import chat_history_bp
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables

load_dotenv()


url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)



app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
#CORS(app, origins=["http://localhost:3000", "https://*.vercel.app"])
#CORS(app, origins=["http://localhost:3000", "https://chat-tfm.vercel.app", "https://*.vercel.app"])
# More permissive CORS configuration
CORS(app, origins=[
    "http://localhost:3000", 
    "https://*.vercel.app", 
    "https://chat-tfm.vercel.app",
    "https://*.vercel.app"
], 
allow_headers=["Content-Type", "Authorization"],
methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
# Register blueprints
app.register_blueprint(chat_bp, url_prefix='/api')
app.register_blueprint(chat_history_bp, url_prefix='/api')


logging.basicConfig(level=logging.DEBUG)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "RAG Chatbot Backend"}

@app.route('/test-supabase', methods=['GET'])
def test_supabase():
    try:
        response = supabase.from_('chunk_embeddings').select('*').execute()
        return {"status": "connected", "data": response.data}, 200
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}, 500

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test connection to both Supabase and RAG service"""
    try:
        # Test Supabase connection
        supabase_response = supabase.from_('chunk_embeddings').select('*').limit(1).execute()
        
        return {
            "status": "success",
            "message": "All services connected",
            "supabase": "connected",
            "timestamp": datetime.now().isoformat()
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "RAG Chatbot Backend API is running. Use /api/chat for chat functionality.", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

