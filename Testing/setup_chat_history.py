#!/usr/bin/env python3
"""
Setup script for chat history table
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("❌ Missing Supabase environment variables")
    print("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def check_table_exists():
    """Check if chat_history table exists"""
    try:
        # Try to select from the table
        response = supabase.table('chat_history').select('*').limit(1).execute()
        print("✅ chat_history table exists")
        return True
    except Exception as e:
        print(f"❌ chat_history table does not exist: {e}")
        return False

def create_table():
    """Create the chat_history table"""
    print("\n📋 Creating chat_history table...")
    
    # SQL to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS public.chat_history (
        id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id text NOT NULL,
        conversation_id text NOT NULL,
        message_content text NOT NULL,
        sender text NOT NULL CHECK (sender IN ('user', 'bot')),
        ragas_metrics jsonb NULL,
        created_at timestamp with time zone NOT NULL DEFAULT now()
    );
    """
    
    try:
        # Execute the SQL
        response = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ chat_history table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        print("\n📝 Please run the following SQL manually in your Supabase SQL Editor:")
        print(create_table_sql)
        return False

def test_insert():
    """Test inserting a message"""
    print("\n🧪 Testing message insertion...")
    
    import uuid
    
    test_data = {
        "user_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "message_content": "This is a test message",
        "sender": "user"
    }
    
    try:
        response = supabase.table('chat_history').insert(test_data).execute()
        if response.data:
            print(f"✅ Test message inserted successfully: {response.data[0]['id']}")
            
            # Clean up test data
            supabase.table('chat_history').delete().eq('id', response.data[0]['id']).execute()
            print("✅ Test data cleaned up")
            return True
        else:
            print("❌ No data returned from insert")
            return False
    except Exception as e:
        print(f"❌ Failed to insert test message: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Chat History Table Setup")
    print("=" * 40)
    
    # Check if table exists
    if not check_table_exists():
        # Try to create the table
        if not create_table():
            print("\n❌ Setup failed. Please create the table manually.")
            return
    
    # Test insertion
    if test_insert():
        print("\n🎉 Setup completed successfully!")
        print("The chat_history table is ready to use.")
    else:
        print("\n⚠️ Setup completed with warnings.")
        print("The table exists but there might be permission issues.")

if __name__ == "__main__":
    main() 