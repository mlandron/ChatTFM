-- Fix RLS policies for chat_history table
-- Run this in your Supabase SQL Editor

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

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check 
FROM pg_policies 
WHERE tablename = 'chat_history'; 