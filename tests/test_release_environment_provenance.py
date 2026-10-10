import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.verify_release_environment import (
    resolve_release_environment,
    verify_historical_release,
)


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




    def test_pull_request_merge_checkout_treats_new_archive_as_candidate(self):
        temp=tempfile.TemporaryDirectory(); root=Path(temp.name); self.addCleanup(temp.cleanup)
        subprocess.check_call(["git","init","-q","-b","main"],cwd=root)
        (root/"requirements.lock").write_text("urllib3==2.7.0\n")
        commit(root,"base")
        git(root,"checkout","-q","-b","candidate")
        archive_rel="public/archive/2026-10-09/repro_bundle.json"
        archive=root/archive_rel; archive.parent.mkdir(parents=True)
        archive.write_text("{}\n")
        candidate=commit(root,"candidate archive")
        git(root,"checkout","-q","main")
        (root/"base-only.txt").write_text("base advanced\n")
        commit(root,"base advance")
        git(
            root,
            "-c","user.name=Test",
            "-c","user.email=test@example.invalid",
            "merge","-q","--no-ff","candidate","-m","synthetic pull request merge",
        )
        head=git(root,"rev-parse","HEAD")
        full_history=git(root,"log","--format=%H","--reverse","--",archive_rel).splitlines()
        mainline_history=git(
            root,"log","--first-parent","--format=%H","--reverse","--",archive_rel
        ).splitlines()
        self.assertEqual(full_history[0],candidate)
        self.assertNotEqual(candidate,head)
        self.assertEqual(mainline_history[0],head)
        profile={
            "lock_path":"runtime/requirements-2026-10-05.lock",
            "lock_sha256":"b"*64,
            "profile_id":"test-active-runtime",
        }
        with mock.patch(
            "scripts.verify_release_environment.verify_profile",
            return_value=profile,
        ):
            resolved=resolve_release_environment(root,"2026-10-09")
        self.assertEqual(resolved["mode"],"active_runtime_candidate")
        self.assertEqual(resolved["lock_sha256"],"b"*64)

    def test_resolver_keeps_historical_release_on_strict_mainline_path(self):
        temp,root,trusted=self.make_repo(); self.addCleanup(temp.cleanup)
        profile={
            "lock_path":"runtime/requirements-2026-10-05.lock",
            "lock_sha256":"b"*64,
            "profile_id":"test-active-runtime",
        }
        with mock.patch(
            "scripts.verify_release_environment.verify_profile",
            return_value=profile,
        ):
            resolved=resolve_release_environment(root,"2026-09-18")
        self.assertEqual(resolved["mode"],"historical_release")
        self.assertEqual(resolved["publication_sha"],trusted["publication_sha"])
        self.assertEqual(resolved["generator_sha"],trusted["generator_sha"])


    def test_resolver_uses_generator_active_runtime_lock_for_historical_release(self):
        temp=tempfile.TemporaryDirectory(); root=Path(temp.name); self.addCleanup(temp.cleanup)
        subprocess.check_call(["git","init","-q","-b","main"],cwd=root)
        legacy=b"urllib3==2.7.0\n"
        runtime=b"urllib3==2.8.0\n"
        runtime_path="runtime/requirements-2026-10-05.lock"
        (root/"requirements.lock").write_bytes(legacy)
        (root/"runtime").mkdir()
        (root/runtime_path).write_bytes(runtime)
        (root/"runtime/active-environment.json").write_text(
            json.dumps({
                "lock_path": runtime_path,
                "legacy_frozen_lock": {"path": "requirements.lock"},
            })+"\n"
        )
        generator=commit(root,"runtime generator")
        week="2026-10-09"
        bundle={
            "score_week":week,
            "pipeline_git_sha":generator,
            "requirements_lock_sha256":hashlib.sha256(runtime).hexdigest(),
        }
        archive_rel=f"public/archive/{week}/repro_bundle.json"
        archive=root/archive_rel; archive.parent.mkdir(parents=True)
        archive.write_text(json.dumps(bundle,sort_keys=True)+"\n")
        publication=commit(root,"runtime publication")
        (root/runtime_path).write_text("urllib3==2.9.0\n")
        commit(root,"later runtime upgrade")
        profile={
            "lock_path":runtime_path,
            "lock_sha256":"c"*64,
            "profile_id":"current-runtime",
        }
        with mock.patch(
            "scripts.verify_release_environment.verify_profile",
            return_value=profile,
        ):
            resolved=resolve_release_environment(root,week)
        self.assertEqual(resolved["mode"],"historical_release")
        self.assertEqual(resolved["publication_sha"],publication)
        self.assertEqual(resolved["generator_sha"],generator)
        self.assertEqual(resolved["lock_path"],runtime_path)
        self.assertEqual(
            resolved["lock_sha256"], hashlib.sha256(runtime).hexdigest()
        )


if __name__=="__main__": unittest.main()
