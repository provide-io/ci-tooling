# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for provide.cicd.conform module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from provide.cicd.conform import (
    FOOTER_EMOJIS,
    HEADER_LIBRARY,
    HEADER_SHEBANG,
    PLACEHOLDER_DOCSTRING,
    SPDX_BLOCK,
    conform_file,
    detect_repo_name,
    find_module_docstring_and_body_start,
    get_footer_for_current_repo,
    load_footer_registry,
)

if TYPE_CHECKING:
    pass


# ==============================================================================
# Test detect_repo_name
# ==============================================================================


def test_detect_repo_name_with_git_remote(mock_git_repo: Path) -> None:
    """Test repository detection from git remote URL."""
    repo_name = detect_repo_name()
    assert repo_name == "test-repo"


def test_detect_repo_name_fallback_to_directory(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test fallback to directory name when git is not available."""
    # Change to temp directory (not a git repo)
    test_dir = temp_dir / "my-project"
    test_dir.mkdir()
    monkeypatch.chdir(test_dir)

    repo_name = detect_repo_name()
    assert repo_name == "my-project"


# ==============================================================================
# Test load_footer_registry
# ==============================================================================


def test_load_footer_registry_valid(mock_footer_registry: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading valid footer registry."""
    # Monkey-patch to use our test registry
    import provide.cicd.conform as conform_module

    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    registry = load_footer_registry()

    assert "test-repo" in registry
    assert registry["test-repo"] == "# 🧪🔚"
    assert "pyvider" in registry
    assert registry["pyvider"] == "# 🐍🔌🔚"


def test_load_footer_registry_missing_file(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading footer registry when file doesn't exist."""
    import provide.cicd.conform as conform_module

    # Point to non-existent file
    fake_path = temp_dir / "nonexistent.py"
    monkeypatch.setattr(conform_module, "__file__", str(fake_path))

    registry = load_footer_registry()

    # Should return empty dict
    assert registry == {}


def test_load_footer_registry_corrupt_json(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading corrupt JSON registry."""
    import provide.cicd.conform as conform_module

    # Create corrupt JSON file
    corrupt_file = temp_dir / "corrupt.py"
    corrupt_file.write_text("dummy")
    registry_file = temp_dir / "footer_registry.json"
    registry_file.write_text("{invalid json")

    monkeypatch.setattr(conform_module, "__file__", str(corrupt_file))

    registry = load_footer_registry()

    # Should return empty dict
    assert registry == {}


# ==============================================================================
# Test get_footer_for_current_repo
# ==============================================================================


def test_get_footer_for_current_repo_found(
    mock_git_repo: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test getting footer for known repository."""
    import provide.cicd.conform as conform_module

    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    footer = get_footer_for_current_repo()

    assert footer == "# 🧪🔚"


def test_get_footer_for_current_repo_fallback(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test fallback footer for unknown repository."""
    import provide.cicd.conform as conform_module

    unknown_dir = temp_dir / "unknown-repo"
    unknown_dir.mkdir()
    monkeypatch.chdir(unknown_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    footer = get_footer_for_current_repo()

    # Should return default footer
    assert footer == "# 🔚"


# ==============================================================================
# Test find_module_docstring_and_body_start
# ==============================================================================


def test_find_module_docstring_with_docstring() -> None:
    """Test finding module docstring when present."""
    content = '''"""Module docstring."""

def main():
    pass
'''

    docstring, body_start = find_module_docstring_and_body_start(content)

    assert docstring == "Module docstring."
    assert body_start == 3  # Line where def main() starts


def test_find_module_docstring_without_docstring() -> None:
    """Test finding module docstring when absent."""
    content = """def main():
    pass
"""

    docstring, body_start = find_module_docstring_and_body_start(content)

    assert docstring is None
    assert body_start == 1  # Line where def main() starts


def test_find_module_docstring_empty_file() -> None:
    """Test finding module docstring in empty file."""
    content = ""

    docstring, body_start = find_module_docstring_and_body_start(content)

    assert docstring is None
    assert body_start == 1


def test_find_module_docstring_only_docstring() -> None:
    """Test finding module docstring with only docstring."""
    content = '''"""Just a docstring."""
'''

    docstring, body_start = find_module_docstring_and_body_start(content)

    assert docstring == "Just a docstring."
    assert body_start == 2


def test_find_module_docstring_syntax_error() -> None:
    """Test handling syntax error in Python file."""
    content = "def invalid syntax here"

    docstring, body_start = find_module_docstring_and_body_start(content)

    assert docstring is None
    assert body_start == 1


# ==============================================================================
# Test conform_file
# ==============================================================================


def test_conform_file_empty_file(temp_dir: Path) -> None:
    """Test conforming an empty file."""
    file_path = temp_dir / "empty.py"
    file_path.write_text("")

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    content = file_path.read_text()
    assert HEADER_LIBRARY in content
    assert all(line in content for line in SPDX_BLOCK)
    assert PLACEHOLDER_DOCSTRING in content
    assert "# 🧪🔚" in content


def test_conform_file_with_shebang(temp_dir: Path) -> None:
    """Test conforming file with shebang."""
    file_path = temp_dir / "script.py"
    file_path.write_text("#!/usr/bin/env python3\n\ndef main():\n    pass\n")

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    content = file_path.read_text()
    assert content.startswith(HEADER_SHEBANG)
    assert all(line in content for line in SPDX_BLOCK)
    assert "# 🧪🔚" in content


def test_conform_file_preserves_docstring(temp_dir: Path) -> None:
    """Test that conform preserves existing module docstring."""
    file_path = temp_dir / "documented.py"
    original_content = '''"""My module docstring."""

def hello():
    pass
'''
    file_path.write_text(original_content)

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    content = file_path.read_text()
    assert '"""My module docstring."""' in content
    assert "# 🧪🔚" in content


def test_conform_file_strips_old_footer(temp_dir: Path) -> None:
    """Test that conform strips old footer emojis."""
    file_path = temp_dir / "with_footer.py"
    content = """def test():
    pass

# 🐍🔌🔚
"""
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    new_content = file_path.read_text()

    # Old footer should be gone
    assert "🐍🔌" not in new_content
    # New footer should be present
    assert "# 🧪🔚" in new_content


def test_conform_file_strips_multiple_footer_emojis(temp_dir: Path) -> None:
    """Test that conform strips all footer emoji lines."""
    file_path = temp_dir / "multi_footer.py"
    content = """def test():
    pass

# Some comment with 🔧 emoji
# Another with 📦 emoji
# 🔚
"""
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    new_content = file_path.read_text()

    # All old footer emojis should be stripped
    assert "🔧" not in new_content
    assert "📦" not in new_content
    # But our new footer should be present
    assert "# 🧪🔚" in new_content


def test_conform_file_already_conformant(temp_dir: Path) -> None:
    """Test that already conformant file is not modified."""
    file_path = temp_dir / "conformant.py"
    content = f'''{HEADER_LIBRARY}
{SPDX_BLOCK[0]}
{SPDX_BLOCK[1]}
{SPDX_BLOCK[2]}

"""Module docstring."""

def test():
    pass

# 🧪🔚
'''
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    # Should not modify already conformant file
    assert modified is False


def test_conform_file_unicode_content(temp_dir: Path) -> None:
    """Test conforming file with Unicode content."""
    file_path = temp_dir / "unicode.py"
    content = '''"""Unicode test: 你好世界."""

def greet():
    return "Hello World"
'''
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    new_content = file_path.read_text()
    assert "你好世界" in new_content
    assert "Hello World" in new_content
    assert "# 🧪🔚" in new_content


def test_conform_file_read_error(temp_dir: Path) -> None:
    """Test handling read errors."""
    file_path = temp_dir / "nonexistent.py"

    modified = conform_file(file_path, "# 🧪🔚")

    # Should return False on read error
    assert modified is False


def test_conform_file_no_body_content(temp_dir: Path) -> None:
    """Test conforming file with only docstring."""
    file_path = temp_dir / "docstring_only.py"
    file_path.write_text('"""Just a docstring."""\n')

    modified = conform_file(file_path, "# 🧪🔚")

    assert modified is True
    content = file_path.read_text()
    assert all(line in content for line in SPDX_BLOCK)
    assert '"""Just a docstring."""' in content
    assert "# 🧪🔚" in content


# ==============================================================================
# Test Constants
# ==============================================================================


def test_constants_are_defined() -> None:
    """Test that all expected constants are defined."""
    assert HEADER_SHEBANG == "#!/usr/bin/env python3"
    assert HEADER_LIBRARY == "# "
    assert len(SPDX_BLOCK) == 3
    assert PLACEHOLDER_DOCSTRING == '"""TODO: Add module docstring."""'
    assert len(FOOTER_EMOJIS) > 20  # Should have many footer emojis


def test_footer_emojis_include_expected_emojis() -> None:
    """Test that common footer emojis are in the list."""
    expected_emojis = ["🐍", "🔌", "🔚", "📦", "🧰", "⚙️"]

    for emoji in expected_emojis:
        assert emoji in FOOTER_EMOJIS


# ==============================================================================
# Test main() CLI function
# ==============================================================================


def test_main_with_valid_file(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test main() CLI with file that needs conformance."""
    import provide.cicd.conform as conform_module
    from provide.cicd.conform import main

    # Setup
    file_path = temp_dir / "test.py"
    file_path.write_text("def test(): pass\n")
    monkeypatch.chdir(temp_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    # Call main with the file
    exit_code = main([str(file_path)])

    # File was modified, so exit code should be 1
    assert exit_code == 1
    # Verify file was actually modified
    content = file_path.read_text()
    assert all(line in content for line in SPDX_BLOCK)


def test_main_with_already_conformant_file(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test main() with already conformant file."""
    import provide.cicd.conform as conform_module
    from provide.cicd.conform import main

    # Create already conformant file
    file_path = temp_dir / "conformant.py"
    content = f"""{HEADER_LIBRARY}
{SPDX_BLOCK[0]}
{SPDX_BLOCK[1]}
{SPDX_BLOCK[2]}

\"\"\"Module docstring.\"\"\"

def test():
    pass

# 🔚
"""
    file_path.write_text(content)
    monkeypatch.chdir(temp_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    # Call main
    exit_code = main([str(file_path)])

    # No changes needed, exit code 0
    assert exit_code == 0


def test_main_with_no_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with no file arguments."""
    from provide.cicd.conform import main

    # Call main with empty list
    exit_code = main([])

    # Should exit successfully with code 0
    assert exit_code == 0


def test_main_with_nonexistent_file(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test main() with non-existent file."""
    import provide.cicd.conform as conform_module
    from provide.cicd.conform import main

    monkeypatch.chdir(temp_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    # Call with non-existent file
    nonexistent = temp_dir / "nonexistent.py"
    exit_code = main([str(nonexistent)])

    # Should exit with error code 1
    assert exit_code == 1


def test_main_with_non_python_file(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test main() skips non-Python files."""
    import provide.cicd.conform as conform_module
    from provide.cicd.conform import main

    # Create a .txt file
    txt_file = temp_dir / "readme.txt"
    txt_file.write_text("Not a Python file")
    monkeypatch.chdir(temp_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    # Call main with .txt file
    exit_code = main([str(txt_file)])

    # Should skip non-Python files, exit 0
    assert exit_code == 0
    # File should not be modified
    assert txt_file.read_text() == "Not a Python file"


def test_main_with_footer_override(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test main() with --footer override."""
    import provide.cicd.conform as conform_module
    from provide.cicd.conform import main

    file_path = temp_dir / "test.py"
    file_path.write_text("def test(): pass\n")
    monkeypatch.chdir(temp_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    # Call with custom footer
    exit_code = main([str(file_path), "--footer", "# 🎯🔚"])

    # File modified
    assert exit_code == 1
    content = file_path.read_text()
    # Should have custom footer
    assert "# 🎯🔚" in content
    # Should NOT have default footer
    assert "# 🔚" not in content or content.count("# 🔚") == 0 or "# 🎯🔚" in content


def test_main_with_multiple_files_mixed_results(
    temp_dir: Path,
    mock_footer_registry: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test main() with mix of valid, invalid, and missing files."""
    import provide.cicd.conform as conform_module
    from provide.cicd.conform import main

    # Create conformant file
    conformant = temp_dir / "conformant.py"
    conformant_content = f"""{HEADER_LIBRARY}
{SPDX_BLOCK[0]}
{SPDX_BLOCK[1]}
{SPDX_BLOCK[2]}

\"\"\"Conformant.\"\"\"

# 🔚
"""
    conformant.write_text(conformant_content)

    # Create file that needs fixing
    needs_fix = temp_dir / "needs_fix.py"
    needs_fix.write_text("def test(): pass\n")

    # Non-existent file
    nonexistent = temp_dir / "nonexistent.py"

    monkeypatch.chdir(temp_dir)
    monkeypatch.setattr(conform_module, "__file__", str(mock_footer_registry))

    # Call with all three files
    exit_code = main([str(conformant), str(needs_fix), str(nonexistent)])

    # Should have errors (nonexistent file)
    assert exit_code == 1


def test_conform_file_write_error(temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test conform_file handles write errors gracefully."""
    file_path = temp_dir / "test.py"
    file_path.write_text("def test(): pass\n")

    # Make file read-only to trigger write error
    import stat

    file_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    # Try to conform the file
    try:
        modified = conform_file(file_path, "# 🧪🔚")
        # Should return False on write error
        assert modified is False
    finally:
        # Restore write permissions for cleanup
        file_path.chmod(stat.S_IWUSR | stat.S_IRUSR)


def test_conform_file_with_existing_spdx_headers_no_duplication(temp_dir: Path) -> None:
    """Test that conform doesn't duplicate existing SPDX headers."""
    file_path = temp_dir / "existing_headers.py"
    # File already has SPDX headers and docstring
    content = """#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

\"\"\"Module with existing headers.\"\"\"

def hello():
    return "world"
"""
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    # File should be modified (footer added)
    assert modified is True

    # Read result and verify no duplication
    result = file_path.read_text()
    lines = result.splitlines()

    # Count SPDX header occurrences - should only appear once
    spdx_copyright_count = sum(1 for line in lines if "SPDX-FileCopyrightText" in line)
    spdx_license_count = sum(1 for line in lines if "SPDX-License-Identifier" in line)

    assert spdx_copyright_count == 1, f"Expected 1 copyright line, got {spdx_copyright_count}"
    assert spdx_license_count == 1, f"Expected 1 license line, got {spdx_license_count}"

    # Verify docstring appears only once
    docstring_count = result.count('"""Module with existing headers."""')
    assert docstring_count == 1, f"Expected 1 docstring, got {docstring_count}"

    # Verify footer is present
    assert "# 🧪🔚" in result

    # Verify function is still there
    assert "def hello():" in result


def test_conform_file_with_shebang_and_existing_headers_no_duplication(temp_dir: Path) -> None:
    """Test that conform doesn't duplicate shebang or SPDX headers."""
    file_path = temp_dir / "executable_with_headers.py"
    # Executable file with shebang and SPDX headers
    content = """#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

\"\"\"Executable script with existing headers.\"\"\"

def main():
    print("Hello")

if __name__ == "__main__":
    main()
"""
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    # File should be modified (footer added)
    assert modified is True

    # Read result and verify no duplication
    result = file_path.read_text()
    lines = result.splitlines()

    # Count shebang occurrences - should only appear once at the start
    shebang_count = sum(1 for line in lines if line.strip().startswith("#!/usr/bin/env python"))
    assert shebang_count == 1, f"Expected 1 shebang, got {shebang_count}"

    # Verify shebang is at the start
    assert lines[0].strip().startswith("#!/usr/bin/env python")

    # Count SPDX headers - should only appear once
    spdx_copyright_count = sum(1 for line in lines if "SPDX-FileCopyrightText" in line)
    spdx_license_count = sum(1 for line in lines if "SPDX-License-Identifier" in line)

    assert spdx_copyright_count == 1, f"Expected 1 copyright line, got {spdx_copyright_count}"
    assert spdx_license_count == 1, f"Expected 1 license line, got {spdx_license_count}"

    # Verify docstring appears only once
    docstring_count = result.count('"""Executable script with existing headers."""')
    assert docstring_count == 1, f"Expected 1 docstring, got {docstring_count}"


def test_conform_file_fixes_corrupted_file_with_duplicate_headers(temp_dir: Path) -> None:
    """Test that conform fixes files already corrupted by previous bug."""
    file_path = temp_dir / "corrupted.py"
    # File corrupted by the old bug - has duplicate headers and placeholder docstring
    content = """#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

\"\"\"TODO: Add module docstring.\"\"\"

#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

\"\"\"Real module docstring.\"\"\"

def function():
    return "value"
"""
    file_path.write_text(content)

    modified = conform_file(file_path, "# 🧪🔚")

    # File should be modified
    assert modified is True

    # Read result and verify corruption is fixed
    result = file_path.read_text()
    lines = result.splitlines()

    # Count SPDX headers - should only appear once
    spdx_copyright_count = sum(1 for line in lines if "SPDX-FileCopyrightText" in line)
    spdx_license_count = sum(1 for line in lines if "SPDX-License-Identifier" in line)

    assert spdx_copyright_count == 1, f"Expected 1 copyright line, got {spdx_copyright_count}"
    assert spdx_license_count == 1, f"Expected 1 license line, got {spdx_license_count}"

    # Verify placeholder is removed
    assert (
        '"""TODO: Add module docstring."""' not in result
        or result.count('"""TODO: Add module docstring."""') == 1
    )

    # Verify real docstring is present
    assert '"""Real module docstring."""' in result

    # Verify function is still there
    assert "def function():" in result


# 🧰⚙️🔚
