"""Invite authentication and durable quotas for semi-public LoopMaster betas."""

from __future__ import annotations

import base64
from contextlib import closing
import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def hash_invite_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Invite:
    invite_id: str
    code_sha256: str
    daily_limit: int
    max_active_jobs: int


class BetaAccess:
    cookie_name = "loopmaster_beta"

    def __init__(self, output_dir: str):
        self.enabled = _truthy(os.environ.get("LOOPMASTER_PUBLIC_BETA"))
        self.secure_cookie = _truthy(
            os.environ.get("LOOPMASTER_SECURE_COOKIE", "1" if self.enabled else "0")
        )
        self.cookie_ttl = max(
            300, int(os.environ.get("LOOPMASTER_AUTH_TTL_SECONDS", "604800"))
        )
        self._secret = os.environ.get("LOOPMASTER_AUTH_SECRET", "").encode("utf-8")
        self._invites: dict[str, Invite] = {}
        self._lock = threading.Lock()
        state_dir = os.path.join(output_dir, ".loopmaster")
        self.database_path = os.path.join(state_dir, "beta-access.sqlite3")
        if not self.enabled:
            return
        if len(self._secret) < 32:
            raise RuntimeError(
                "LOOPMASTER_AUTH_SECRET must contain at least 32 characters in public beta mode"
            )
        invites_path = os.environ.get("LOOPMASTER_INVITES_FILE", "").strip()
        if not invites_path:
            raise RuntimeError("LOOPMASTER_INVITES_FILE is required in public beta mode")
        with open(invites_path, encoding="utf-8") as source:
            document = json.load(source)
        for item in document.get("invites", []):
            if not item.get("enabled", True):
                continue
            invite = Invite(
                invite_id=str(item["id"]),
                code_sha256=str(item["code_sha256"]).lower(),
                daily_limit=max(1, int(item.get("daily_limit", 20))),
                max_active_jobs=max(1, int(item.get("max_active_jobs", 1))),
            )
            self._invites[invite.invite_id] = invite
        if not self._invites:
            raise RuntimeError("The public beta invite file contains no enabled invites")
        os.makedirs(state_dir, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS quota_usage ("
                "invite_id TEXT NOT NULL, day TEXT NOT NULL, used INTEGER NOT NULL, "
                "PRIMARY KEY(invite_id, day))"
            )

    def _connect(self):
        return sqlite3.connect(self.database_path, timeout=10, isolation_level=None)

    @staticmethod
    def _encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    @staticmethod
    def _decode(value: str) -> bytes:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    def authenticate_code(self, code: str) -> Invite | None:
        candidate = hash_invite_code(code.strip())
        for invite in self._invites.values():
            if hmac.compare_digest(candidate, invite.code_sha256):
                return invite
        return None

    def issue_token(self, invite_id: str) -> str:
        payload = json.dumps(
            {"invite": invite_id, "exp": int(time.time()) + self.cookie_ttl},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded = self._encode(payload)
        signature = hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).digest()
        return f"{encoded}.{self._encode(signature)}"

    def verify_token(self, token: str | None) -> Invite | None:
        if not token or "." not in token:
            return None
        encoded, supplied = token.split(".", 1)
        expected = hmac.new(self._secret, encoded.encode("ascii"), hashlib.sha256).digest()
        try:
            if not hmac.compare_digest(expected, self._decode(supplied)):
                return None
            payload = json.loads(self._decode(encoded))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return self._invites.get(str(payload.get("invite", "")))

    def reserve_generation(self, invite: Invite, units: int = 1) -> tuple[bool, int]:
        units = max(1, int(units))
        day = datetime.now(timezone.utc).date().isoformat()
        with self._lock, closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT used FROM quota_usage WHERE invite_id=? AND day=?",
                (invite.invite_id, day),
            ).fetchone()
            used = int(row[0]) if row else 0
            if used + units > invite.daily_limit:
                connection.rollback()
                return False, 0
            connection.execute(
                "INSERT INTO quota_usage(invite_id, day, used) VALUES(?, ?, ?) "
                "ON CONFLICT(invite_id, day) DO UPDATE SET used=used+excluded.used",
                (invite.invite_id, day, units),
            )
            connection.commit()
            return True, invite.daily_limit - used - units

    def refund_generation(self, invite_id: str, units: int = 1) -> None:
        units = max(1, int(units))
        day = datetime.now(timezone.utc).date().isoformat()
        with self._lock, closing(self._connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "UPDATE quota_usage SET used=MAX(0, used-?) WHERE invite_id=? AND day=?",
                (units, invite_id, day),
            )
            connection.commit()

    def quota_status(self, invite: Invite) -> dict:
        day = datetime.now(timezone.utc).date().isoformat()
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT used FROM quota_usage WHERE invite_id=? AND day=?",
                (invite.invite_id, day),
            ).fetchone()
        used = int(row[0]) if row else 0
        return {
            "daily_limit": invite.daily_limit,
            "used_today": used,
            "remaining_today": max(0, invite.daily_limit - used),
            "max_active_jobs": invite.max_active_jobs,
        }
