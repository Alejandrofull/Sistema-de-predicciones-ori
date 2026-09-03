from supabase import (
    Client,
    create_client
)

from app.config.settings import (
    SUPABASE_KEY,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL
)


# ==========================================
# CLIENTE PÚBLICO / RESTRINGIDO
# ==========================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==========================================
# CLIENTE ADMINISTRATIVO DEL BACKEND
# ==========================================

supabase_admin: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)