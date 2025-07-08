-- Function to get user conversations with latest message info
CREATE OR REPLACE FUNCTION get_user_conversations(user_id_param UUID)
RETURNS TABLE (
    conversation_id UUID,
    last_message TEXT,
    last_message_sender TEXT,
    last_message_time TIMESTAMPTZ,
    message_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH conversation_summaries AS (
        SELECT 
            ch.conversation_id,
            ch.message_content as last_message,
            ch.sender as last_message_sender,
            ch.created_at as last_message_time,
            COUNT(*) OVER (PARTITION BY ch.conversation_id) as message_count,
            ROW_NUMBER() OVER (PARTITION BY ch.conversation_id ORDER BY ch.created_at DESC) as rn
        FROM chat_history ch
        WHERE ch.user_id = user_id_param
    )
    SELECT 
        cs.conversation_id,
        cs.last_message,
        cs.last_message_sender,
        cs.last_message_time,
        cs.message_count
    FROM conversation_summaries cs
    WHERE cs.rn = 1
    ORDER BY cs.last_message_time DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS (Row Level Security) on chat_history table
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to see only their own messages
CREATE POLICY "Users can view own messages" ON chat_history
    FOR SELECT USING (auth.uid() = user_id);

-- Policy to allow users to insert their own messages
CREATE POLICY "Users can insert own messages" ON chat_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy to allow users to delete their own messages
CREATE POLICY "Users can delete own messages" ON chat_history
    FOR DELETE USING (auth.uid() = user_id);

-- Policy to allow users to update their own messages
CREATE POLICY "Users can update own messages" ON chat_history
    FOR UPDATE USING (auth.uid() = user_id);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON chat_history TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_conversations(UUID) TO authenticated; 