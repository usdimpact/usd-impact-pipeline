from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.IGNORECASE)
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")


class GitHubActionsPinningTests(unittest.TestCase):
    def test_external_actions_use_immutable_commit_shas(self) -> None:
        violations: list[str] = []
        external_uses = 0

        for workflow in sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")]):
            for line_number, line in enumerate(
                workflow.read_text(encoding="utf-8").splitlines(), start=1
            ):
                match = USES_RE.match(line)
                if not match:
                    continue
                target = match.group(1).strip('"\'')
                if target.startswith("./") or target.startswith("docker://"):
                    continue
                external_uses += 1
                if "@" not in target:
                    violations.append(
                        f"{workflow.relative_to(ROOT)}:{line_number}: missing action ref: {target}"
                    )
                    continue
                ref = target.rsplit("@", 1)[1]
                if not SHA40_RE.fullmatch(ref):
                    violations.append(
                        f"{workflow.relative_to(ROOT)}:{line_number}: external action must use a 40-char commit SHA: {target}"
                    )

        self.assertGreater(external_uses, 0, "No external GitHub Actions were inspected")
        self.assertEqual(violations, [], "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
