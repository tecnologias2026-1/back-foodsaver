from db import supabase

response = supabase.table("ingredientes").select("*").execute()

print(response.data)