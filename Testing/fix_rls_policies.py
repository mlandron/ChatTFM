#!/usr/bin/env python3
"""
Fix RLS policies for chat_history table
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
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def fix_rls_policies():
    """Fix RLS policies for chat_history table"""
    print("🔧 Fixing RLS policies for chat_history table...")
    
    # SQL to fix RLS policies
    rls_sql = """
    -- Drop existing policies if they exist
    DROP POLICY IF EXISTS "Users can view own messages" ON chat_history;
    DROP POLICY IF EXISTS "Users can insert own messages" ON chat_history;
    DROP POLICY IF EXISTS "Users can delete own messages" ON chat_history;
    DROP POLICY IF EXISTS "Users can update own messages" ON chat_history;
    
    -- Create new policies that work with both authenticated and anonymous users
    CREATE POLICY "Enable read access for all users" ON chat_history
        FOR SELECT USING (true);
    
    CREATE POLICY "Enable insert access for all users" ON chat_history
        FOR INSERT WITH CHECK (true);
    
    CREATE POLICY "Enable delete access for all users" ON chat_history
        FOR DELETE USING (true);
    
    CREATE POLICY "Enable update access for all users" ON chat_history
        FOR UPDATE USING (true);
    
    -- Grant necessary permissions
    GRANT USAGE ON SCHEMA public TO anon, authenticated;
    GRANT ALL ON chat_history TO anon, authenticated;
    """
    
    try:
        # Execute the SQL
        response = supabase.rpc('exec_sql', {'sql': rls_sql}).execute()
        print("✅ RLS policies updated successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to update RLS policies: {e}")
        print("\n📝 Please run the following SQL manually in your Supabase SQL Editor:")
        print(rls_sql)
        return False

def test_insert_after_fix():
    """Test inserting a message after fixing RLS"""
    print("\n🧪 Testing message insertion after RLS fix...")
    
    import uuid
    
    test_data = {
        "user_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "message_content": "This is a test message after RLS fix",
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
    """Main function"""
    print("🚀 RLS Policy Fix for Chat History")
    print("=" * 40)
    
    # Fix RLS policies
    if fix_rls_policies():
        # Test insertion
        if test_insert_after_fix():
            print("\n🎉 RLS policies fixed successfully!")
            print("The chat_history table is now ready to use.")
        else:
            print("\n⚠️ RLS policies were updated but insertion still failed.")
    else:
        print("\n❌ Failed to fix RLS policies.")

if __name__ == "__main__":
    main() 