import os

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PUBLIC_KEY_RAW = os.getenv("VAPID_PUBLIC_KEY_RAW", "")

VAPID_CLAIMS = {
    "sub": os.getenv("VAPID_SUBJECT", "mailto:soporte@tu-dominio.com"),
}