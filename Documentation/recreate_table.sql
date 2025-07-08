-- Recreate chat_history table with correct structure
-- Run this in your Supabase SQL Editor

-- Drop the existing table
DROP TABLE IF EXISTS chat_history;

-- Create the table with text fields for user_id and conversation_id
CREATE TABLE public.chat_history (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id text NOT NULL, -- Changed from uuid to text to support anonymous users
    conversation_id text NOT NULL, -- Changed from uuid to text
    message_content text NOT NULL,
    sender text NOT NULL CHECK (sender IN ('user', 'bot')),
    ragas_metrics jsonb NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now()
    -- Removed foreign key constraint to support anonymous users
);

-- Enable RLS
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Create simple policies that allow all operations
CREATE POLICY "Enable read access for all users" ON chat_history
    FOR SELECT USING (true);

CREATE POLICY "Enable insert access for all users" ON chat_history
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable delete access for all users" ON chat_history
    FOR DELETE USING (true);

CREATE POLICY "Enable update access for all users" ON chat_history
    FOR UPDATE USING (true);

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON chat_history TO anon, authenticated;

-- Create indexes for better performance
CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX idx_chat_history_conversation_id ON chat_history(conversation_id);
CREATE INDEX idx_chat_history_created_at ON chat_history(created_at);

-- Verify the table structure
\d chat_history; 