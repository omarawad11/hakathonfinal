import os
import mysql.connector
from datetime import datetime, timezone
from pathlib import Path
# from zoneinfo import ZoneInfo  # available in Python 3.9+

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS faces_logs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_name VARCHAR(255) NOT NULL,
  ip VARCHAR(45) NOT NULL,
  status BOOLEAN NOT NULL,
  accuracy DOUBLE,
  date_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_date_time (date_time),
  INDEX idx_user_time (user_name, date_time)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
"""

def _get_connection():

    cfg = {
        "user": os.getenv("DO_DB_USER", "doadmin"),
        "password": os.getenv("DO_DB_PASSWORD", "AVNS_yd5BvB5BFbr4yRmTfpA"),
        "host": os.getenv("DO_DB_HOST", "db-mysql-nyc3-51062-do-user-24398900-0.l.db.ondigitalocean.com"),
        "port": int(os.getenv("DO_DB_PORT", "25060")),
        "database": os.getenv("DO_DB_NAME", "defaultdb"),
    }
    if not cfg["password"]:
        raise RuntimeError("DO_DB_PASSWORD is not set.")

    # SSL settings: DigitalOcean requires SSL. Prefer validating with CA if provided.
    ssl_ca = os.getenv("DO_DB_SSL_CA")  # e.g., "/etc/ssl/certs/ca-certificate.crt"
    if ssl_ca:
        cfg.update({"ssl_ca": ssl_ca})
    else:
        # Fall back to encrypted connection without supplying CA.
        # If your server enforces full verification, download the CA and set DO_DB_SSL_CA.
        cfg.update({"ssl_disabled": False})

    return mysql.connector.connect(**cfg)

def init_db():
    """Create the faces_logs table if it doesn't exist."""
    cnx = _get_connection()
    try:
        with cnx.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        cnx.commit()
    finally:
        cnx.close()

def _coerce_bool(value) -> bool:
    """Accept bool, 0/1, or common truthy/falsey strings."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int,)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "t", "yes", "y"}:
            return True
        if v in {"0", "false", "f", "no", "n"}:
            return False
    raise ValueError(f"Cannot interpret status={value!r} as boolean.")

# Example: use UTC

def log_face_event(user_name: str, ip: str, status, accuracy: float, tz: str = "UTC") -> int:
    """
    Insert a log row with accuracy into the faces_logs table.
    - status: True/False, 1/0, or 'true'/'false'
    - accuracy: float between 0.0 and 1.0
    - tz: timezone string (e.g., 'UTC', 'Asia/Amman')
    """
    status_bool = _coerce_bool(status)

    # Sanity check for accuracy
    if not (0.0 <= accuracy <= 1.0):
        raise ValueError(f"accuracy must be between 0 and 1, got {accuracy}")

    # Timestamp
    try:
        # now = datetime.now(ZoneInfo(tz))
        now = datetime.now()
    except Exception:
        # Fallback to UTC if tz data missing
        now = datetime.now(timezone.utc)

    cnx = _get_connection()
    try:
        with cnx.cursor() as cur:
            cur.execute(
                """
                INSERT INTO faces_logs (user_name, ip, status, accuracy, date_time)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_name, ip, status_bool, accuracy, now),
            )
            inserted_id = cur.lastrowid
        cnx.commit()
        return inserted_id
    finally:
        cnx.close()

import mysql.connector
from typing import List, Dict, Any

def fetch_face_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch the most recent rows from faces_logs, ordered by id descending.
    Default limit is 50 rows.
    Returns a list of dictionaries.
    """
    cnx = _get_connection()
    try:
        with cnx.cursor(dictionary=True) as cur:
            cur.execute(
                f"SELECT * FROM defaultdb.faces_logs ORDER BY id DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()
        return rows
    finally:
        cnx.close()

def fetch_users(limit: int = 50, templates_dir: str = "user_templates") -> List[Dict[str, Any]]:
    """
    Collect user entries from .npy files in `templates_dir`.

    Each returned dict has:
      - 'name': filename without the .npy extension
      - 'template_path': absolute path to the .npy file

    Args:
        limit: Maximum number of users to return (non-negative).
        templates_dir: Directory to search (searched recursively).

    Returns:
        List of dictionaries with keys 'name' and 'template_path'.
        Empty list if the directory doesn't exist or no matches found.
    """
    base = Path(templates_dir)

    if not base.is_dir():
        # Directory missing or not a folder → nothing to return
        return []

    # Find all .npy files (recursively), ignore hidden files
    npy_files = [
        p for p in base.rglob("*.npy")
        if p.is_file() and not p.name.startswith(".")
    ]

    # Sort deterministically by filename (case-insensitive)
    npy_files.sort(key=lambda p: p.name.lower())

    # Clamp limit to non-negative
    limit = max(0, int(limit))
    users: List[Dict[str, Any]] = [
        {
            "name": p.stem              # filename without extension
        }
        for p in npy_files[:limit]
    ]

    return users

def delete_user(name: str, templates_dir: str = "user_templates", recursive: bool = True) -> int:
    """
    Delete .npy file(s) whose filename (without extension) equals `name` inside `templates_dir`.

    Args:
        name: The target filename stem to delete (e.g., 'omar' deletes 'omar.npy').
        templates_dir: Directory to search.
        recursive: If True, search subdirectories; if False, only the top level.

    Returns:
        The number of files deleted (0 if none found).
    """
    base = Path(templates_dir)
    if not base.is_dir() or not name:
        return 0

    iterator = base.rglob("*.npy") if recursive else base.glob("*.npy")
    targets = [p for p in iterator if p.is_file() and p.stem == name]

    deleted = 0
    for p in targets:
        try:
            p.unlink()
            deleted += 1
        except FileNotFoundError:
            # Already gone—skip
            continue
        except PermissionError as e:
            # Bubble up a clear error message; let caller handle it
            raise PermissionError(f"Cannot delete '{p}': {e}") from e

    return deleted

def update_last_user(name: str) -> None:
    cnx = _get_connection()
    cursor = cnx.cursor()
    try:
        query = """
        UPDATE last_user
        SET user_name = %s
        WHERE id = 1
        """
        cursor.execute(query, (name,))
        cnx.commit()
    finally:
        cursor.close()
        cnx.close()

def get_last_user():
    cnx = _get_connection()
    cursor = cnx.cursor(dictionary=True)
    try:
        query = """
        SELECT user_name
        FROM last_user
        WHERE id = 1
        """
        cursor.execute(query)
        return cursor.fetchone()
    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    # One-time setup: create table if needed
    # init_db()

    # Example usage
    # rid = log_face_event("alice", "203.0.113.42", False)
    # print("Inserted row id:", rid)

    # print(fetch_face_logs())
    # print(get_last_user())
    print(update_last_user("omar"))
