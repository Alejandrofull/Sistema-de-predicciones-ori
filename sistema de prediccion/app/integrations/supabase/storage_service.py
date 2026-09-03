from mimetypes import guess_type
from pathlib import Path

from app.integrations.supabase.client import (
    supabase_admin
)


class SupabaseStorageService:

    def __init__(
        self,
        bucket: str
    ):
        if not bucket:
            raise ValueError(
                "El nombre del bucket es obligatorio"
            )

        self.bucket = bucket

    def upload_file(
        self,
        local_path: Path,
        remote_path: str,
        content_type: str | None = None
    ) -> str:

        local_path = Path(
            local_path
        )

        if not local_path.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: {local_path}"
            )

        if not local_path.is_file():
            raise ValueError(
                "La ruta proporcionada "
                "no corresponde a un archivo"
            )

        remote_path = self._normalize_path(
            remote_path
        )

        if not content_type:
            guessed_type, _ = guess_type(
                local_path.name
            )

            content_type = (
                guessed_type
                or "application/octet-stream"
            )

        file_options = {
            "upsert": "false",
            "content-type": content_type
        }

        with open(
            local_path,
            "rb"
        ) as file:

            supabase_admin.storage.from_(
                self.bucket
            ).upload(
                path=remote_path,
                file=file,
                file_options=file_options
            )

        return remote_path

    def download_bytes(
        self,
        remote_path: str
    ) -> bytes:

        remote_path = self._normalize_path(
            remote_path
        )

        response = (
            supabase_admin.storage
            .from_(self.bucket)
            .download(
                remote_path
            )
        )

        if isinstance(
            response,
            bytes
        ):
            return response

        if isinstance(
            response,
            bytearray
        ):
            return bytes(
                response
            )

        raise RuntimeError(
            "Supabase no devolvió "
            "el archivo en formato bytes"
        )

    def create_signed_url(
        self,
        remote_path: str,
        expires_in: int = 3600
    ) -> str:

        remote_path = self._normalize_path(
            remote_path
        )

        if expires_in <= 0:
            raise ValueError(
                "expires_in debe ser mayor que 0"
            )

        response = (
            supabase_admin.storage
            .from_(self.bucket)
            .create_signed_url(
                remote_path,
                expires_in
            )
        )

        if isinstance(
            response,
            dict
        ):
            signed_url = (
                response.get(
                    "signedURL"
                )
                or response.get(
                    "signed_url"
                )
            )

            if signed_url:
                return signed_url

        signed_url = getattr(
            response,
            "signed_url",
            None
        )

        if signed_url:
            return signed_url

        raise RuntimeError(
            "No se pudo generar "
            "la URL firmada"
        )

    def remove_file(
        self,
        remote_path: str
    ) -> None:

        remote_path = self._normalize_path(
            remote_path
        )

        supabase_admin.storage.from_(
            self.bucket
        ).remove(
            [
                remote_path
            ]
        )

    def exists(
        self,
        folder: str,
        filename: str
    ) -> bool:

        folder = (
            folder
            .replace("\\", "/")
            .strip("/")
        )

        files = (
            supabase_admin.storage
            .from_(self.bucket)
            .list(folder)
        )

        for item in files:

            if isinstance(
                item,
                dict
            ):
                item_name = item.get(
                    "name"
                )

            else:
                item_name = getattr(
                    item,
                    "name",
                    None
                )

            if item_name == filename:
                return True

        return False

    @staticmethod
    def _normalize_path(
        path: str
    ) -> str:

        normalized = (
            path
            .replace("\\", "/")
            .lstrip("/")
        )

        if not normalized:
            raise ValueError(
                "La ruta remota no puede estar vacía"
            )

        return normalized