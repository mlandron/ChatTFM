import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

try:
    response = supabase.from_('chunk_embeddings').select('*').execute()
    print("Connection successful:", response.data[:1])
except Exception as e:
    print("Connection failed:", e)