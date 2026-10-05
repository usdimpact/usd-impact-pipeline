import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_release_environment import verify_historical_release


def git(root,*args):
    return subprocess.check_output(["git",*args],cwd=root,text=True).strip()


def commit(root,message):
    subprocess.check_call(["git","add","."],cwd=root)
    subprocess.check_call(["git","-c","user.name=Test","-c","user.email=test@example.invalid","commit","-m",message],cwd=root,stdout=subprocess.DEVNULL)
    return git(root,"rev-parse","HEAD")


class ReleaseEnvironmentProvenanceTests(unittest.TestCase):
    def make_repo(self):
        temp=tempfile.TemporaryDirectory(); root=Path(temp.name)
        subprocess.check_call(["git","init","-q","-b","main"],cwd=root)
        lock=b"urllib3==2.7.0\n"; (root/"requirements.lock").write_bytes(lock)
        generator=commit(root,"generator")
        bundle={"score_week":"2026-09-18","pipeline_git_sha":generator,"requirements_lock_sha256":hashlib.sha256(lock).hexdigest()}
        p=root/"public/archive/2026-09-18"; p.mkdir(parents=True)
        raw=(json.dumps(bundle,sort_keys=True)+"\n").encode(); (p/"repro_bundle.json").write_bytes(raw)
        publication=commit(root,"publication")
        (root/"later.txt").write_text("later\n"); trusted_base=commit(root,"later")
        trusted={"week":"2026-09-18","publication_sha":publication,"generator_sha":generator,"trusted_base_sha":trusted_base,"bundle_path":"public/archive/2026-09-18/repro_bundle.json","bundle_sha256":hashlib.sha256(raw).hexdigest(),"lock_path":"requirements.lock","lock_sha256":hashlib.sha256(lock).hexdigest()}
        return temp,root,trusted

    def test_historical_release_uses_generator_lock_not_current_lock(self):
        temp,root,trusted=self.make_repo(); self.addCleanup(temp.cleanup)
        (root/"requirements.lock").write_text("urllib3==2.8.0\n")
        self.assertEqual(verify_historical_release(root,trusted)["status"],"verified_historical_release_environment")

    def test_changed_bundle_digest_is_rejected(self):
        temp,root,trusted=self.make_repo(); self.addCleanup(temp.cleanup)
        trusted["bundle_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"bundle digest mismatch"): verify_historical_release(root,trusted)

    def test_wrong_generator_is_rejected(self):
        temp,root,trusted=self.make_repo(); self.addCleanup(temp.cleanup)
        trusted["generator_sha"]=trusted["publication_sha"]
        with self.assertRaisesRegex(ValueError,"generator SHA mismatch"): verify_historical_release(root,trusted)

    def test_path_escape_is_rejected(self):
        temp,root,trusted=self.make_repo(); self.addCleanup(temp.cleanup)
        trusted["lock_path"]="../requirements.lock"
        with self.assertRaisesRegex(ValueError,"safe relative path"): verify_historical_release(root,trusted)


if __name__=="__main__": unittest.main()
