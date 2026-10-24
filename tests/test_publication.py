"""Offline validation of the exact manual publication plan; never invokes hf."""

import fnmatch
import os
from pathlib import Path
import shlex
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync-huggingface.yml"


class PublicationSafetyTests(unittest.TestCase):
    def test_manual_static_upload_stages_only_reviewed_files_and_deletes_exact_old_paths(
        self,
    ):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        triggers = workflow.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertEqual(
            [
                line.strip()
                for line in triggers.splitlines()
                if line.startswith("  ") and not line.startswith("    ")
            ],
            ["workflow_dispatch:"],
        )
        self.assertIn("confirm_publication:", triggers)
        self.assertIn("required: true", triggers)
        self.assertIn("type: boolean", triggers)
        self.assertIn("default: false", triggers)
        self.assertIn(
            "if: github.ref == 'refs/heads/master' && inputs.confirm_publication == true",
            workflow,
        )
        self.assertIn("huggingface_hub==2.3.0", workflow)
        permissions = (
            workflow.split("\npermissions:\n", 1)[1].split("\njobs:", 1)[0].strip()
        )
        self.assertEqual(permissions, "contents: read")
        self.assertIn(
            "id-token: write", workflow
        )  # only the explicitly dispatched publication job
        self.assertIn("persist-credentials: false", workflow)

        # Execute only the workflow's local staging code in a synthetic temporary tree.
        staging = textwrap.dedent(
            workflow.split("python - <<'PY'\n", 1)[1].split("\n          PY", 1)[0]
        )
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "hf-space"
            source.mkdir()
            for name in ("README.md", "index.html"):
                (source / name).write_bytes((ROOT / "hf-space" / name).read_bytes())
            for name in (".env", "contacts.csv", "app.py", "requirements.txt"):
                (source / name).write_text("Synthetic sentinel: must not be published")
            runner_temp = base / "runner"
            runner_temp.mkdir()
            try:
                os.chdir(base)
                with patch.dict(os.environ, {"RUNNER_TEMP": str(runner_temp)}):
                    exec(compile(staging, str(WORKFLOW), "exec"), {})
            finally:
                os.chdir(original)
            staged = runner_temp / "space-source"
            self.assertEqual(
                {p.name for p in staged.iterdir()}, {"README.md", "index.html"}
            )
            for name in ("README.md", "index.html"):
                self.assertEqual(
                    (staged / name).read_bytes(),
                    (ROOT / "hf-space" / name).read_bytes(),
                )
            self.assertIn("\nsdk: static\n", (staged / "README.md").read_text())

        commands = [
            line.strip()
            for line in workflow.splitlines()
            if line.strip().startswith("hf ")
        ]
        self.assertEqual(len(commands), 1)
        arguments = shlex.split(commands[0])
        self.assertEqual(
            arguments[:3], ["hf", "upload", "AlirezaBelal/iran-contact-data-pipeline"]
        )
        self.assertEqual(arguments[3:5], ["$RUNNER_TEMP/space-source", "."])
        self.assertEqual(arguments[arguments.index("--repo-type") + 1], "space")
        patterns = [
            arguments[i + 1] for i, arg in enumerate(arguments) if arg == "--delete"
        ]
        self.assertEqual(patterns, ["app.py", "requirements.txt"])
        # Model the observed remote tree plus unrelated files: only the two reviewed paths match.
        remote_paths = [
            ".gitattributes",
            "README.md",
            "index.html",
            "app.py",
            "requirements.txt",
            "unrelated.txt",
            "folder/app.py",
        ]
        removed = {
            path
            for path in remote_paths
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
        }
        self.assertEqual(removed, {"app.py", "requirements.txt"})
        self.assertFalse((ROOT / "hf-space" / "app.py").exists())
        self.assertFalse((ROOT / "hf-space" / "requirements.txt").exists())
