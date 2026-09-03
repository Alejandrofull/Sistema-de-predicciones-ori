import os

from dotenv import load_dotenv


load_dotenv()


# ==========================================
# SUPABASE
# ==========================================

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)

SUPABASE_SERVICE_KEY = os.getenv(
    "SUPABASE_SERVICE_KEY"
)


# ==========================================
# DATABASE
# ==========================================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


# ==========================================
# JWT
# ==========================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)

REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv(
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "7"
    )
)


# ==========================================
# VALIDACIONES
# ==========================================

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL no está configurado"
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY no está configurado"
    )

if not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "SUPABASE_SERVICE_KEY no está configurado"
    )

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no está configurado"
    )

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY no está configurado"
    )