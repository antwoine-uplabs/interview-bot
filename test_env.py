import os
from dotenv import load_dotenv

load_dotenv()

print("Supabase URL:", os.environ.get("SUPABASE_URL"))
print("Supabase Key:", os.environ.get("SUPABASE_KEY")[:10] + "..." if os.environ.get("SUPABASE_KEY") else None)
print("Supabase Service Role Key:", os.environ.get("SUPABASE_SERVICE_ROLE_KEY")[:10] + "..." if os.environ.get("SUPABASE_SERVICE_ROLE_KEY") else None)