from supabase import create_client

SUPABASE_URL = "https://hsmrqmyieqcvlyyznhji.supabase.co"
SUPABASE_KEY = "sb_publishable_UtIX5k1aJRYWTwmDYm5mQQ_oDRo-Asd"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
