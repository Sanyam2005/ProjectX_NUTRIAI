"""Image storage with two implementations behind one interface.

LocalStorage writes to ./uploads. AzureBlobStorage is used automatically if
AZURE_STORAGE_CONNECTION_STRING is set. Swapping storage backends is a
single-line change in `get_storage()`.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol

from app.config import get_settings


class ImageStorage(Protocol):
    async def save(self, content: bytes, *, content_type: str, filename: str | None = None) -> str: ...


class LocalStorage:
    def __init__(self, root: str | Path = "uploads") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, *, content_type: str, filename: str | None = None) -> str:
        ext = _extension_for(content_type, filename)
        key = f"{uuid.uuid4().hex}{ext}"
        path = self.root / key
        path.write_bytes(content)
        # Served by FastAPI StaticFiles at /uploads/<key>
        return f"/uploads/{key}"


class AzureBlobStorage:
    def __init__(self, conn_str: str, container: str) -> None:
        # Imported lazily so the package stays optional.
        from azure.storage.blob import BlobServiceClient  # type: ignore

        self._client = BlobServiceClient.from_connection_string(conn_str)
        self._container = container
        try:
            self._client.create_container(container)
        except Exception:
            pass

    async def save(self, content: bytes, *, content_type: str, filename: str | None = None) -> str:
        from azure.storage.blob import ContentSettings  # type: ignore

        ext = _extension_for(content_type, filename)
        key = f"{uuid.uuid4().hex}{ext}"
        blob = self._client.get_blob_client(self._container, key)
        blob.upload_blob(content, overwrite=True, content_settings=ContentSettings(content_type=content_type))
        return blob.url


def _extension_for(content_type: str, filename: str | None) -> str:
    if filename and "." in filename:
        return "." + filename.rsplit(".", 1)[-1].lower()
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
    }
    return mapping.get(content_type.lower(), ".bin")


_storage: ImageStorage | None = None


def get_storage() -> ImageStorage:
    global _storage
    if _storage is not None:
        return _storage
    settings = get_settings()
    if settings.azure_storage_connection_string:
        try:
            _storage = AzureBlobStorage(
                settings.azure_storage_connection_string,
                settings.azure_storage_container,
            )
            return _storage
        except Exception:
            # azure SDK not installed → fall through to local
            pass
    _storage = LocalStorage("uploads")
    return _storage
