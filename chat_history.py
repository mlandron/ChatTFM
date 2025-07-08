import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from flask import Blueprint, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

chat_history_bp = Blueprint('chat_history', __name__)
logger = logging.getLogger(__name__)

def generate_conversation_id() -> str:
    """Generate a unique conversation ID"""
    return str(uuid.uuid4())

def save_message_to_supabase(
    user_id: str,
    conversation_id: str,
    message_content: str,
    sender: str,
    ragas_metrics: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Save a chat message to Supabase chat_history table
    
    Args:
        user_id: The user ID (from auth.uid() or generated for anonymous users)
        conversation_id: The conversation ID
        message_content: The message content
        sender: Either 'user' or 'bot'
        ragas_metrics: Optional RAGAS metrics data
    
    Returns:
        Dict containing the saved message data
    """
    try:
        # Prepare the data for insertion
        message_data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_content": message_content,
            "sender": sender,
            "created_at": datetime.utcnow().isoformat() + "Z"  # ISO format with timezone
        }
        
        # Add ragas_metrics if provided
        if ragas_metrics:
            message_data["ragas_metrics"] = ragas_metrics
        
        logger.info(f"Attempting to save message: {message_data}")
        
        # Insert the message into the chat_history table
        # For now, we'll use a simpler approach without RLS for testing
        response = supabase.table('chat_history').insert(message_data).execute()
        
        if response.data:
            logger.info(f"Message saved successfully: {response.data[0]['id']}")
            return {
                "status": "success",
                "data": response.data[0]
            }
        else:
            logger.error("No data returned from Supabase insert")
            return {
                "status": "error",
                "message": "Failed to save message"
            }
            
    except Exception as e:
        logger.error(f"Error saving message to Supabase: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def get_conversation_messages(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """
    Retrieve all messages for a specific conversation
    
    Args:
        conversation_id: The conversation ID
        user_id: The user ID to filter messages
    
    Returns:
        Dict containing the conversation messages
    """
    try:
        response = supabase.table('chat_history')\
            .select('*')\
            .eq('conversation_id', conversation_id)\
            .eq('user_id', user_id)\
            .order('created_at', desc=False)\
            .execute()
        
        if response.data:
            return {
                "status": "success",
                "data": response.data
            }
        else:
            return {
                "status": "success",
                "data": []
            }
            
    except Exception as e:
        logger.error(f"Error retrieving conversation messages: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def get_user_conversations(user_id: str) -> Dict[str, Any]:
    """
    Get all conversations for a user with their latest messages
    
    Args:
        user_id: The user ID
    
    Returns:
        Dict containing conversations with latest message info
    """
    try:
        # For now, use a simple query instead of the custom function
        # This will get all messages for the user, grouped by conversation
        response = supabase.table('chat_history')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        if response.data:
            # Group messages by conversation_id and get the latest message for each
            conversations = {}
            for msg in response.data:
                conv_id = msg['conversation_id']
                if conv_id not in conversations:
                    conversations[conv_id] = {
                        'conversation_id': conv_id,
                        'last_message': msg['message_content'],
                        'last_message_sender': msg['sender'],
                        'last_message_time': msg['created_at'],
                        'message_count': 1
                    }
                else:
                    conversations[conv_id]['message_count'] += 1
            
            # Convert to list and sort by last message time
            conversation_list = list(conversations.values())
            conversation_list.sort(key=lambda x: x['last_message_time'], reverse=True)
            
            return {
                "status": "success",
                "data": conversation_list
            }
        else:
            return {
                "status": "success",
                "data": []
            }
            
    except Exception as e:
        logger.error(f"Error retrieving user conversations: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def delete_conversation(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """
    Delete all messages for a specific conversation
    
    Args:
        conversation_id: The conversation ID
        user_id: The user ID to ensure ownership
    
    Returns:
        Dict containing the deletion result
    """
    try:
        response = supabase.table('chat_history')\
            .delete()\
            .eq('conversation_id', conversation_id)\
            .eq('user_id', user_id)\
            .execute()
        
        return {
            "status": "success",
            "message": "Conversation deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# API Endpoints
@chat_history_bp.route('/chat-history/save-message', methods=['POST'])
def save_message():
    """Save a chat message to the database"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['user_id', 'conversation_id', 'message_content', 'sender']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate sender
        if data['sender'] not in ['user', 'bot']:
            return jsonify({"error": "Sender must be 'user' or 'bot'"}), 400
        
        result = save_message_to_supabase(
            user_id=data['user_id'],
            conversation_id=data['conversation_id'],
            message_content=data['message_content'],
            sender=data['sender'],
            ragas_metrics=data.get('ragas_metrics')
        )
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in save_message endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@chat_history_bp.route('/chat-history/conversations/<user_id>', methods=['GET'])
def get_conversations(user_id):
    """Get all conversations for a user"""
    try:
        result = get_user_conversations(user_id)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in get_conversations endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@chat_history_bp.route('/chat-history/conversation/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages_endpoint(conversation_id):
    """Get all messages for a specific conversation"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        result = get_conversation_messages(conversation_id, user_id)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in get_conversation_messages endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@chat_history_bp.route('/chat-history/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation_endpoint(conversation_id):
    """Delete a conversation and all its messages"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400
        
        result = delete_conversation(conversation_id, user_id)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in delete_conversation endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500 