from pathlib import Path

from app.integrations.supabase.storage_service import (
    SupabaseStorageService
)


test_file = Path(
    "storage_test.txt"
)

test_file.write_text(
    "Prueba de Supabase Storage",
    encoding="utf-8"
)


storage = SupabaseStorageService(
    bucket="exports"
)

remote_path = storage.upload_file(
    local_path=test_file,
    remote_path="tests/storage_test.txt",
    content_type="text/plain"
)

print(
    "✅ Archivo subido:"
)
print(remote_path)


url = storage.create_signed_url(
    remote_path,
    expires_in=3600
)

print(
    "✅ URL firmada:"
)
print(url)


test_file.unlink(
    missing_ok=True
)