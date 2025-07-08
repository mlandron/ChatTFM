#!/usr/bin/env python3
"""
Test script for chat history functionality
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
TEST_USER_ID = str(uuid.uuid4())
TEST_CONVERSATION_ID = str(uuid.uuid4())

def test_connection():
    """Test the connection endpoint"""
    print("🔍 Testing connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/test-connection")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connection successful: {data['message']}")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_save_message():
    """Test saving a message"""
    print("\n💾 Testing message save...")
    try:
        message_data = {
            "user_id": TEST_USER_ID,
            "conversation_id": TEST_CONVERSATION_ID,
            "message_content": "Hello, this is a test message!",
            "sender": "user"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat-history/save-message",
            json=message_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message saved successfully: {data['data']['id']}")
            return True
        else:
            print(f"❌ Failed to save message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Save message error: {e}")
        return False

def test_save_bot_message():
    """Test saving a bot message"""
    print("\n🤖 Testing bot message save...")
    try:
        message_data = {
            "user_id": TEST_USER_ID,
            "conversation_id": TEST_CONVERSATION_ID,
            "message_content": "Hello! I'm the bot responding to your test message.",
            "sender": "bot",
            "ragas_metrics": {
                "faithfulness": 0.95,
                "answer_relevancy": 0.88,
                "context_relevancy": 0.92
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat-history/save-message",
            json=message_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Bot message saved successfully: {data['data']['id']}")
            return True
        else:
            print(f"❌ Failed to save bot message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Save bot message error: {e}")
        return False

def test_get_conversation_messages():
    """Test retrieving conversation messages"""
    print("\n📋 Testing get conversation messages...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/chat-history/conversation/{TEST_CONVERSATION_ID}/messages?user_id={TEST_USER_ID}"
        )
        
        if response.status_code == 200:
            data = response.json()
            messages = data['data']
            print(f"✅ Retrieved {len(messages)} messages from conversation")
            for msg in messages:
                print(f"   - {msg['sender']}: {msg['message_content'][:50]}...")
            return True
        else:
            print(f"❌ Failed to get messages: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get messages error: {e}")
        return False

def test_get_user_conversations():
    """Test retrieving user conversations"""
    print("\n👤 Testing get user conversations...")
    try:
        response = requests.get(f"{BASE_URL}/api/chat-history/conversations/{TEST_USER_ID}")
        
        if response.status_code == 200:
            data = response.json()
            conversations = data['data']
            print(f"✅ Retrieved {len(conversations)} conversations for user")
            for conv in conversations:
                print(f"   - Conversation {conv['conversation_id'][:8]}...: {conv['message_count']} messages")
            return True
        else:
            print(f"❌ Failed to get conversations: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get conversations error: {e}")
        return False

def test_chat_with_history():
    """Test the chat endpoint with history saving"""
    print("\n💬 Testing chat with history...")
    try:
        chat_data = {
            "query": "What are the requirements for retirement?",
            "user_id": TEST_USER_ID,
            "conversation_id": TEST_CONVERSATION_ID,
            "embedding_model": "BAAI/bge-m3",
            "top_k": 5,
            "temperature": 0.1,
            "chat_model": "gpt-4o-mini"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat successful: {len(data.get('answer', ''))} characters in response")
            print(f"   Conversation ID: {data.get('conversation_id')}")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def test_delete_conversation():
    """Test deleting a conversation"""
    print("\n🗑️ Testing delete conversation...")
    try:
        response = requests.delete(
            f"{BASE_URL}/api/chat-history/conversation/{TEST_CONVERSATION_ID}?user_id={TEST_USER_ID}"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conversation deleted successfully: {data['message']}")
            return True
        else:
            print(f"❌ Failed to delete conversation: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Delete conversation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Chat History Tests")
    print("=" * 50)
    
    tests = [
        test_connection,
        test_save_message,
        test_save_bot_message,
        test_get_conversation_messages,
        test_get_user_conversations,
        test_chat_with_history,
        test_delete_conversation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chat history functionality is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the setup and try again.")

if __name__ == "__main__":
    main() 