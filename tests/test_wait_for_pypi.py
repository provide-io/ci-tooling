# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Tests for the gate that blocks until a published version is resolvable.

The script decides from the text `pip index versions` prints, so every test
puts a `pip` stub on PATH that prints a chosen fixture. Two real bugs came out
of this parsing during development -- a quiet `grep` SIGPIPE-ing pip under
`pipefail`, and `0.5.3` matching `0.5.30` -- and both have a case here.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release" / "wait-for-pypi.sh"

PRESENT = "pyvider (0.7.0)\nAvailable versions: 0.7.0, 0.6.2, 0.6.1, 0.6.0\n"
ABSENT = "pyvider (0.6.2)\nAvailable versions: 0.6.2, 0.6.1, 0.6.0\n"
# The listing that made an anchorless match wrong: 0.5.3 is not here, 0.5.30 is.
CONFUSABLE = "pyvider (0.5.30)\nAvailable versions: 0.5.30, 0.5.29\n"
PRERELEASE = "pyvider (1.0.0rc1)\nAvailable versions: 1.0.0rc1, 0.9.9\n"
# Reproducing the SIGPIPE needs two things at once: the match has to come early
# enough that a quiet reader stops there, and what follows has to exceed the
# pipe buffer so the writer is still writing when the reader goes. 64 KiB is the
# usual buffer, so this pads well past it *after* the version being sought.
LONG = (
    "pyvider (0.7.0)\nAvailable versions: 0.7.0, "
    + ", ".join(f"0.{n // 100}.{n % 100}" for n in range(20000))
    + "\n"
)


def _stub(bin_dir: Path, *, script: str) -> None:
    bin_dir.mkdir(exist_ok=True)
    pip = bin_dir / "pip"
    pip.write_text(script)
    pip.chmod(0o755)


def _run(
    tmp_path: Path, *, version: str, timeout: str = "1", pip_script: str
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    _stub(bin_dir, script=pip_script)
    return subprocess.run(
        ["bash", str(SCRIPT), "pyvider", version, timeout],
        env={
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "WAIT_FOR_PYPI_INTERVAL": "0",
        },
        capture_output=True,
        text=True,
    )


def _prints(text: str) -> str:
    return f"#!/usr/bin/env bash\ncat <<'EOF'\n{text}EOF\n"


def test_a_published_version_is_resolvable(tmp_path: Path) -> None:
    result = _run(tmp_path, version="0.7.0", pip_script=_prints(PRESENT))

    assert result.returncode == 0
    assert "is resolvable from PyPI" in result.stdout


def test_a_version_the_index_does_not_carry_fails(tmp_path: Path) -> None:
    result = _run(tmp_path, version="0.7.0", pip_script=_prints(ABSENT))

    assert result.returncode == 1
    assert "still not resolvable" in result.stderr


def test_a_longer_version_is_not_a_match(tmp_path: Path) -> None:
    """0.5.3 must not be satisfied by 0.5.30: the gate would pass early."""
    result = _run(tmp_path, version="0.5.3", pip_script=_prints(CONFUSABLE))

    assert result.returncode == 1


def test_that_longer_version_is_still_matched_for_itself(tmp_path: Path) -> None:
    result = _run(tmp_path, version="0.5.30", pip_script=_prints(CONFUSABLE))

    assert result.returncode == 0


def test_a_prerelease_is_matched(tmp_path: Path) -> None:
    result = _run(tmp_path, version="1.0.0rc1", pip_script=_prints(PRERELEASE))

    assert result.returncode == 0


def test_a_present_version_is_not_lost_to_a_broken_pipe(tmp_path: Path) -> None:
    """The regression that read a published version as missing.

    Matching by piping into `grep -q` let the quiet grep exit on the first hit,
    SIGPIPE the writer, and -- under `pipefail` -- report the whole pipeline as
    failed. A long listing is what makes that reachable.
    """
    result = _run(tmp_path, version="0.7.0", pip_script=_prints(LONG))

    assert result.returncode == 0


def test_the_index_catching_up_late_still_passes(tmp_path: Path) -> None:
    """The window the gate exists for: absent, then present on a later attempt."""
    counter = tmp_path / "attempts"
    script = f"""#!/usr/bin/env bash
n=$(cat {counter} 2>/dev/null || echo 0)
echo $((n + 1)) > {counter}
if [ "$n" -ge 2 ]; then
  cat <<'EOF'
{PRESENT}EOF
else
  cat <<'EOF'
{ABSENT}EOF
fi
"""
    result = _run(tmp_path, version="0.7.0", timeout="30", pip_script=script)

    assert result.returncode == 0
    assert int(counter.read_text()) == 3
    assert "not visible yet (attempt 1)" in result.stdout


def test_pip_failing_outright_is_retried_not_fatal(tmp_path: Path) -> None:
    """Before the first upload lands, `pip index versions` exits non-zero."""
    counter = tmp_path / "attempts"
    script = f"""#!/usr/bin/env bash
n=$(cat {counter} 2>/dev/null || echo 0)
echo $((n + 1)) > {counter}
if [ "$n" -ge 1 ]; then
  cat <<'EOF'
{PRESENT}EOF
  exit 0
fi
echo 'ERROR: No matching distribution found for pyvider' >&2
exit 1
"""
    result = _run(tmp_path, version="0.7.0", timeout="30", pip_script=script)

    assert result.returncode == 0
    assert int(counter.read_text()) == 2


def test_the_deadline_is_honoured(tmp_path: Path) -> None:
    result = _run(tmp_path, version="0.7.0", timeout="0", pip_script=_prints(ABSENT))

    assert result.returncode == 1
    assert "after 0s" in result.stderr


@pytest.mark.parametrize("args", [[], ["pyvider"]])
def test_missing_arguments_fail_loudly(tmp_path: Path, args: list[str]) -> None:
    bin_dir = tmp_path / "bin"
    _stub(bin_dir, script=_prints(PRESENT))

    result = subprocess.run(
        ["bash", str(SCRIPT), *args],
        env={**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
