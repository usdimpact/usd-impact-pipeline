import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.execution_environment import EXPECTED_CALLERS, load_profile, parse_lock, verify_profile


class ExecutionEnvironmentTests(unittest.TestCase):
    def make_root(self, active=False):
        temp=tempfile.TemporaryDirectory()
        root=Path(temp.name)
        (root/"runtime").mkdir()
        legacy=b"a==1\nurllib3==2.7.0\n"
        candidate=b"a==1\nurllib3==2.8.0\n"
        (root/"requirements.lock").write_bytes(legacy)
        (root/"runtime/candidate.lock").write_bytes(candidate)
        profile={
            "schema_version":1,
            "profile_id":"test",
            "status":"active_candidate" if active else "candidate_not_active",
            "python":{"implementation":"CPython","major_minor":"3.11"},
            "platform":"ubuntu-24.04",
            "lock_path":"runtime/candidate.lock",
            "legacy_frozen_lock":{
                "path":"requirements.lock",
                "sha256":hashlib.sha256(legacy).hexdigest(),
                "purpose":"frozen_research_and_historical_release_provenance",
            },
            "activation":{
                "active":active,
                "caller_allowlist":sorted(EXPECTED_CALLERS) if active else [],
            },
        }
        path=root/"runtime/profile.json"
        path.write_text(json.dumps(profile),encoding="utf-8")
        return temp,root,path,profile

    def test_candidate_and_legacy_identities_are_distinct(self):
        temp,root,path,_=self.make_root(); self.addCleanup(temp.cleanup)
        report=verify_profile(root,path)
        self.assertEqual(report["status"],"verified_candidate_not_active")
        self.assertFalse(report["active"])

    def test_active_candidate_requires_exact_callers(self):
        temp,root,path,profile=self.make_root(active=True); self.addCleanup(temp.cleanup)
        report=verify_profile(root,path)
        self.assertEqual(report["status"],"verified_active_candidate")
        self.assertTrue(report["active"])
        profile["activation"]["caller_allowlist"].pop()
        path.write_text(json.dumps(profile),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"incomplete or broadened"):
            load_profile(path)

    def test_unknown_field_is_rejected(self):
        temp,_,path,profile=self.make_root(); self.addCleanup(temp.cleanup)
        profile["unexpected"]=True; path.write_text(json.dumps(profile),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"closed schema"): load_profile(path)

    def test_path_escape_is_rejected(self):
        temp,_,path,profile=self.make_root(); self.addCleanup(temp.cleanup)
        profile["lock_path"]="../outside"; path.write_text(json.dumps(profile),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"inside repository"): load_profile(path)

    def test_hash_drift_is_rejected(self):
        temp,root,path,_=self.make_root(); self.addCleanup(temp.cleanup)
        (root/"requirements.lock").write_text("a==1\nurllib3==2.6.0\n")
        with self.assertRaisesRegex(ValueError,"legacy frozen lock hash mismatch"): verify_profile(root,path)

    def test_non_exact_requirement_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"lock"; p.write_text("urllib3>=2.8.0\n")
            with self.assertRaisesRegex(ValueError,"non-exact"): parse_lock(p)

    def test_repository_profile_is_active_candidate(self):
        root=Path(__file__).resolve().parents[1]
        report=verify_profile(root,root/"runtime/active-environment.json")
        self.assertEqual(report["profile_id"],"online-python-2026-10-05")
        self.assertTrue(report["active"])
        self.assertEqual(set(report["caller_allowlist"]), EXPECTED_CALLERS)


if __name__=="__main__": unittest.main()
