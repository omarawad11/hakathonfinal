# pip install boto3
import os
import io
import mimetypes
from typing import Union, Optional, Dict
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError

DO_REGION = "sfo3"
DO_ENDPOINT = f"https://{DO_REGION}.digitaloceanspaces.com"

os.environ["SPACES_KEY"] = "DO009EJ7AWUXAAJ877AV"
os.environ["SPACES_SECRET"] = "/QPnHj0YS9HKRgYnUK1d9hrCG9057KSGtzp1p1uKlJM"

def make_spaces_client(
    key: Optional[str] = None,
    secret: Optional[str] = None,
    region: str = DO_REGION,
    endpoint_url: str = DO_ENDPOINT,
):
    """Create a boto3 client for DigitalOcean Spaces (S3-compatible)."""
    key = key or os.getenv("SPACES_KEY")
    secret = secret or os.getenv("SPACES_SECRET")
    if not key or not secret:
        raise ValueError("Missing credentials. Set SPACES_KEY and SPACES_SECRET env vars or pass key/secret.")
    session = Session()
    return session.client(
        "s3",
        region_name=region,
        endpoint_url=endpoint_url,
        aws_access_key_id=key,
        aws_secret_access_key=secret,
        config=Config(signature_version="s3v4", retries={"max_attempts": 5, "mode": "standard"}),
    )

def upload_to_spaces(
    file_or_bytes: Union[str, bytes, io.BufferedReader, io.BytesIO],
    key: str,
    bucket: str = "faces-logs",
    *,
    public: bool = True,
    content_type: Optional[str] = 'image/jpeg',
    cache_control: Optional[str] = None,
    client=None,
) -> Dict[str, str]:
    """
    Upload a local path, bytes, or file-like object to DigitalOcean Spaces.

    Args:
        file_or_bytes: path to a local file OR raw bytes OR a file-like object.
        key: path/key in the bucket (e.g. 'logs/2025-09-15/app.json').
        bucket: target bucket (defaults to 'faces-logs').
        public: if True, sets ACL to 'public-read' and returns a public URL.
        content_type: override Content-Type; auto-detected if not provided for local files.
        cache_control: optional Cache-Control header (e.g. 'public, max-age=3600').
        client: optional pre-created boto3 S3 client.

    Returns:
        dict with 'bucket', 'key', and 'url' (public URL if public=True, otherwise virtual-hosted URL).
    """
    s3 = client or make_spaces_client()

    # Figure out content type
    if content_type is None and isinstance(file_or_bytes, str):
        guessed, _ = mimetypes.guess_type(file_or_bytes)
        content_type = guessed or "application/octet-stream"
    elif content_type is None:
        content_type = "application/octet-stream"

    extra = {"ContentType": content_type}
    if cache_control:
        extra["CacheControl"] = cache_control
    if public:
        extra["ACL"] = "public-read"

    try:
        if isinstance(file_or_bytes, str):
            # Upload from local path
            s3.upload_file(Filename=file_or_bytes, Bucket=bucket, Key=key, ExtraArgs=extra)
        else:
            # Upload from bytes or file-like
            body = file_or_bytes
            if isinstance(file_or_bytes, bytes):
                body = io.BytesIO(file_or_bytes)
            s3.put_object(Bucket=bucket, Key=key, Body=body, **extra)
    except ClientError as e:
        raise RuntimeError(f"Upload failed: {e}") from e

    # Build URL (virtual-hosted style)
    base = f"https://{bucket}.{DO_REGION}.digitaloceanspaces.com"
    url = f"{base}/{key}"
    return {"bucket": bucket, "key": key, "url": url}

# --- Examples ---
if __name__ == "__main__":
    os.environ["SPACES_KEY"] = "DO009EJ7AWUXAAJ877AV"
    os.environ["SPACES_SECRET"] = "/QPnHj0YS9HKRgYnUK1d9hrCG9057KSGtzp1p1uKlJM"

    local_path = r"C:\Users\aashq\Desktop\FR py\FRDS2\Bill Gates\Bill Gates49_582.jpg"

    info = upload_to_spaces(
        local_path,
        key="Bill_Gates49_582.jpg",  # how it will be named in the bucket
        public=True,  # make it accessible
        content_type="image/jpeg"
    )

    # 2) Upload bytes and make them publicly readable
    # data = b'{"status":"ok"}'
    # info = upload_to_spaces(data, "logs/2025-09-15/status.json", public=True, content_type="application/json")
    print(info["url"])
