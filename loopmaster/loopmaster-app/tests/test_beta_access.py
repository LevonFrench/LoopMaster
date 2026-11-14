import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from beta_access import BetaAccess, hash_invite_code


class BetaAccessTests(unittest.TestCase):
    def build_access(self, directory, daily_limit=2):
        invites = Path(directory) / "invites.json"
        invites.write_text(json.dumps({"invites": [{
            "id": "discord-alpha",
            "code_sha256": hash_invite_code("correct horse battery staple"),
            "daily_limit": daily_limit,
            "max_active_jobs": 1,
            "enabled": True,
        }]}), encoding="utf-8")
        environment = {
            "LOOPMASTER_PUBLIC_BETA": "1",
            "LOOPMASTER_AUTH_SECRET": "s" * 48,
            "LOOPMASTER_INVITES_FILE": str(invites),
        }
        with patch.dict(os.environ, environment, clear=False):
            return BetaAccess(directory)

    def test_signed_cookie_and_bad_code(self):
        with tempfile.TemporaryDirectory() as directory:
            access = self.build_access(directory)
            self.assertIsNone(access.authenticate_code("wrong"))
            invite = access.authenticate_code("correct horse battery staple")
            self.assertEqual(invite.invite_id, "discord-alpha")
            self.assertEqual(access.verify_token(access.issue_token(invite.invite_id)), invite)
            self.assertIsNone(access.verify_token(access.issue_token(invite.invite_id) + "x"))

    def test_daily_quota_is_durable_and_refundable(self):
        with tempfile.TemporaryDirectory() as directory:
            access = self.build_access(directory)
            invite = access.authenticate_code("correct horse battery staple")
            self.assertEqual(access.reserve_generation(invite), (True, 1))
            self.assertEqual(access.reserve_generation(invite), (True, 0))
            self.assertEqual(access.reserve_generation(invite), (False, 0))
            access.refund_generation(invite.invite_id)
            self.assertEqual(access.reserve_generation(invite), (True, 0))

    def test_quota_counts_generated_variants_not_http_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            access = self.build_access(directory, daily_limit=8)
            invite = access.authenticate_code("correct horse battery staple")
            self.assertEqual(access.reserve_generation(invite, 4), (True, 4))
            self.assertEqual(access.reserve_generation(invite, 5), (False, 0))
            access.refund_generation(invite.invite_id, 4)
            self.assertEqual(access.reserve_generation(invite, 8), (True, 0))


if __name__ == "__main__":
    unittest.main()
