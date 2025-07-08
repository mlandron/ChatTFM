# Supabase Setup for Chat History

This guide will help you set up the Supabase database with the chat history functionality.

## 1. Create the Chat History Table

Run the following SQL in your Supabase SQL Editor:

```sql
CREATE TABLE public.chat_history (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid NOT NULL DEFAULT auth.uid(), -- Automatically links to the logged-in user (regular or anonymous)
  conversation_id uuid NOT NULL,
  message_content text NOT NULL,
  sender text NOT NULL CHECK (sender IN ('user', 'bot')),
  ragas_metrics jsonb NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  -- This constraint ensures data integrity and connects to the central auth system
  CONSTRAINT chat_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);
```

## 2. Create the Database Function

Run the following SQL to create the function for getting user conversations:

```sql
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
```

## 3. Set Up Row Level Security (RLS)

Run the following SQL to enable RLS and create policies:

```sql
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
```

## 4. Environment Variables

Make sure you have the following environment variables set in your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key

# OpenAI Configuration
OPEN_AI_KEY=your_openai_api_key
```

## 5. Testing the Setup

After setting up the database, you can test the connection by:

1. Starting your backend server
2. Making a GET request to `/api/test-connection`
3. The response should show "All services connected"

## 6. API Endpoints

The following endpoints are now available:

- `POST /api/chat` - Send a chat message (now saves to history)
- `POST /api/chat-history/save-message` - Save a message manually
- `GET /api/chat-history/conversations/{user_id}` - Get user conversations
- `GET /api/chat-history/conversation/{conversation_id}/messages?user_id={user_id}` - Get conversation messages
- `DELETE /api/chat-history/conversation/{conversation_id}?user_id={user_id}` - Delete a conversation

## 7. Frontend Integration

The frontend now includes:

- Chat history panel accessible via the history button
- New conversation button
- Automatic saving of all chat messages
- Ability to load previous conversations
- Delete conversation functionality

## 8. Anonymous Users

For anonymous users (users without Supabase authentication), the system:

- Generates a unique user ID stored in localStorage
- Uses this ID for all chat history operations
- Maintains conversation history across browser sessions

## 9. Troubleshooting

### Common Issues:

1. **Permission Denied**: Make sure RLS policies are correctly set up
2. **Function Not Found**: Ensure the `get_user_conversations` function is created
3. **Connection Errors**: Verify your Supabase URL and service key
4. **CORS Issues**: Check that your frontend domain is allowed in Supabase settings

### Debug Steps:

1. Check the browser console for frontend errors
2. Check the backend logs for API errors
3. Test the Supabase connection directly in the SQL editor
4. Verify environment variables are correctly set 