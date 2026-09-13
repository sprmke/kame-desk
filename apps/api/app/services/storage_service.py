import uuid

import boto3
from botocore.client import Config

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}

RECORDING_CONTENT_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
}


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version="s3v4"),
    )


def create_presigned_upload(
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    content_type: str,
    file_size_bytes: int,
) -> tuple[str, str]:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported content type")
    if file_size_bytes > 2_000_000:
        raise ValueError("File too large")

    ext = content_type.split("/")[-1]
    object_key = f"clinics/{clinic_id}/doctors/{doctor_id}/signature.{ext}"
    client = _client()

    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": object_key,
            "ContentType": content_type,
            "ContentLength": file_size_bytes,
        },
        ExpiresIn=300,
        HttpMethod="PUT",
    )
    return url, object_key


def create_clinic_logo_upload(
    clinic_id: uuid.UUID,
    content_type: str,
    file_size_bytes: int,
) -> tuple[str, str]:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported content type")
    if file_size_bytes > 2_000_000:
        raise ValueError("File too large")

    ext = content_type.split("/")[-1]
    if ext == "jpeg":
        ext = "jpg"
    object_key = f"clinics/{clinic_id}/logo.{ext}"
    client = _client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": object_key,
            "ContentType": content_type,
            "ContentLength": file_size_bytes,
        },
        ExpiresIn=300,
        HttpMethod="PUT",
    )
    return url, object_key


PATIENT_FILE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf",
}


def create_patient_file_upload(
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    file_id: uuid.UUID,
    content_type: str,
    file_size_bytes: int,
) -> tuple[str, str]:
    if content_type not in PATIENT_FILE_TYPES:
        raise ValueError("Unsupported content type")
    if file_size_bytes > 20_000_000:
        raise ValueError("File too large")

    ext = content_type.split("/")[-1]
    if ext == "jpeg":
        ext = "jpg"
    object_key = f"clinics/{clinic_id}/patients/{patient_id}/files/{file_id}.{ext}"
    client = _client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": object_key,
            "ContentType": content_type,
            "ContentLength": file_size_bytes,
        },
        ExpiresIn=900,
        HttpMethod="PUT",
    )
    return url, object_key


def create_presigned_download(object_key: str) -> str:
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": object_key},
        ExpiresIn=300,
    )


def upload_object_bytes(object_key: str, body: bytes, content_type: str) -> str:
    client = _client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
        Body=body,
        ContentType=content_type,
    )
    return object_key


def create_recording_upload(
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    recording_id: uuid.UUID,
    content_type: str,
    file_size_bytes: int,
) -> tuple[str, str]:
    if content_type not in RECORDING_CONTENT_TYPES:
        raise ValueError("Unsupported audio type")
    if file_size_bytes > 50_000_000:
        raise ValueError("File too large")

    ext = content_type.split("/")[-1]
    if ext == "x-wav":
        ext = "wav"
    object_key = (
        f"clinics/{clinic_id}/appointments/{appointment_id}/recordings/{recording_id}.{ext}"
    )
    client = _client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": object_key,
            "ContentType": content_type,
            "ContentLength": file_size_bytes,
        },
        ExpiresIn=900,
        HttpMethod="PUT",
    )
    return url, object_key


def download_object_bytes(object_key: str) -> tuple[bytes, str]:
    client = _client()
    obj = client.get_object(Bucket=settings.s3_bucket, Key=object_key)
    body = obj["Body"].read()
    content_type = obj.get("ContentType") or "application/octet-stream"
    return body, content_type


def delete_object(object_key: str) -> None:
    client = _client()
    client.delete_object(Bucket=settings.s3_bucket, Key=object_key)
