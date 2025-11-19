#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Pre-commit hook to enforce SPDX headers and footer conformance.

This hook automatically detects the repository and applies the correct
footer pattern from the central registry. No manual --footer specification needed!

Usage as pre-commit hook:
    The hook is automatically invoked by pre-commit on Python files.

Usage standalone:
    python -m provide.cicd.conform [files...]
"""

import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys

from provide.foundation.console.output import perr, pout

# --- Protocol Constants ---

HEADER_SHEBANG = "#!/usr/bin/env python3"
HEADER_LIBRARY = "# "
SPDX_BLOCK = [
    "# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.",
    "# SPDX-License-Identifier: Apache-2.0",
    "#",
]
PLACEHOLDER_DOCSTRING = '"""TODO: Add module docstring."""'

# Footer emojis to detect and strip
FOOTER_EMOJIS = [
    "🏗️",
    "🐍",
    "🧱",
    "🐝",
    "📁",
    "🍽️",
    "📖",
    "🧪",
    "✅",
    "🧩",
    "🔧",
    "🌊",
    "🪢",
    "🔌",
    "📞",
    "📄",
    "⚙️",
    "🥣",
    "🔬",
    "🔼",
    "🌶️",
    "📦",
    "🧰",
    "🌍",
    "🪄",
    "🔚",
]

# --- Auto-Detection Logic ---


def detect_repo_name() -> str:
    """Auto-detect repository name from git remote or directory name.

    Returns:
        Repository name (e.g., 'pyvider', 'provide-foundation')
    """
    # Try git remote first
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        remote_url = result.stdout.strip()

        # Extract repo name from various Git URL formats:
        # - https://github.com/provide-io/pyvider.git
        # - git@github.com:provide-io/pyvider.git
        # - /path/to/pyvider.git

        repo_name = remote_url.rstrip("/").split("/")[-1]
        repo_name = repo_name.removesuffix(".git")

        if repo_name:
            return repo_name
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: use current directory name
    return Path.cwd().name


def load_footer_registry() -> dict:
    """Load the footer registry from JSON file.

    Returns:
        Dictionary mapping repo names to footer patterns
    """
    registry_path = Path(__file__).parent / "footer_registry.json"

    try:
        with registry_path.open() as f:
            data = json.load(f)
            return data.get("repositories", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        perr(f"Warning: Could not load footer registry: {e}")
        return {}


def get_footer_for_current_repo() -> str:
    """Get the correct footer pattern for the current repository.

    Returns:
        Footer string (e.g., '# 🐍🔌🔚')
    """
    repo_name = detect_repo_name()
    registry = load_footer_registry()

    footer = registry.get(repo_name, "# 🔚")  # Default fallback

    return footer


# --- Conformance Logic (from provide-testkit/scripts/conform.py) ---


def find_module_docstring_and_body_start(content: str) -> tuple[str | None, int]:
    """Parse Python source to find module docstring and code body start.

    Returns:
        Tuple of (docstring, line_number_where_body_starts)
    """
    try:
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)

        if not tree.body:
            return docstring, len(content.splitlines()) + 1

        first_node = tree.body[0]
        start_lineno = first_node.lineno

        # If first node is docstring, code starts after it
        if (
            isinstance(first_node, ast.Expr)
            and isinstance(first_node.value, ast.Constant)
            and isinstance(first_node.value.value, str)
        ):
            start_lineno = tree.body[1].lineno if len(tree.body) > 1 else len(content.splitlines()) + 1

        return docstring, start_lineno
    except SyntaxError:
        # Invalid Python, treat as no docstring
        return None, 1


def _clean_header_lines(lines: list[str]) -> list[str]:
    """Remove shebang, SPDX headers, and placeholder docstrings from lines.

    Args:
        lines: List of file lines with newlines

    Returns:
        Cleaned lines without headers
    """
    cleaned_lines = []
    skip_next_empty = False

    for _i, line in enumerate(lines):
        stripped = line.strip()

        # Skip shebang
        if stripped.startswith("#!"):
            skip_next_empty = True
            continue

        # Skip SPDX header lines
        if stripped.startswith("# SPDX-") or stripped == "#":
            skip_next_empty = True
            continue

        # Skip placeholder docstring if found
        if stripped == '"""TODO: Add module docstring."""':
            skip_next_empty = True
            continue

        # Skip one empty line after headers
        if skip_next_empty and stripped == "":
            skip_next_empty = False
            continue

        skip_next_empty = False
        cleaned_lines.append(line)

    return cleaned_lines


def _remove_footer_emojis(body_content: str) -> str:
    """Remove lines containing footer emojis from body content.

    Args:
        body_content: File body content

    Returns:
        Body content without footer emoji lines
    """
    body_lines_stripped = body_content.splitlines()
    cleaned_body_lines = []
    for line in body_lines_stripped:
        has_footer_emoji = any(emoji in line for emoji in FOOTER_EMOJIS)
        if not has_footer_emoji:
            cleaned_body_lines.append(line)
    return "\n".join(cleaned_body_lines).rstrip()


def _construct_file_content(header_first_line: str, docstring_str: str, body_content: str, footer: str) -> str:
    """Construct the final file content with header, docstring, body, and footer.

    Args:
        header_first_line: First line of header (shebang or comment)
        docstring_str: Module docstring
        body_content: File body content
        footer: Footer string

    Returns:
        Final file content
    """
    final_header = "\n".join([header_first_line, *SPDX_BLOCK])

    if body_content:
        return f"{final_header}\n\n{docstring_str}\n\n{body_content}\n\n{footer}\n"
    return f"{final_header}\n\n{docstring_str}\n\n{footer}\n"


def conform_file(filepath: Path, footer: str) -> bool:
    """Apply header and footer conformance to a single Python file.

    Args:
        filepath: Path to Python file
        footer: Footer string to apply

    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        original_content = content
        lines = content.splitlines(keepends=True)
    except (OSError, UnicodeDecodeError) as e:
        perr(f"Error reading {filepath}: {e}")
        return False

    if not lines:
        # Empty file - add minimal structure
        final_content = (
            "\n".join([HEADER_LIBRARY, *SPDX_BLOCK]) + "\n\n" + PLACEHOLDER_DOCSTRING + "\n\n" + footer + "\n"
        )
        filepath.write_text(final_content, encoding="utf-8")
        return True

    # Determine if file has shebang (before any headers)
    is_executable = lines[0].strip().startswith("#!")
    header_first_line = HEADER_SHEBANG if is_executable else HEADER_LIBRARY

    # Strip existing SPDX headers and shebang to get clean content
    cleaned_lines = _clean_header_lines(lines)
    cleaned_content = "".join(cleaned_lines)

    # Extract docstring and code body from cleaned content
    docstring, body_start_lineno = find_module_docstring_and_body_start(cleaned_content)
    docstring_str = PLACEHOLDER_DOCSTRING if docstring is None else f'"""{docstring}"""'

    # Extract code body (everything after docstring)
    cleaned_lines_list = cleaned_content.splitlines(keepends=True)
    body_lines = cleaned_lines_list[body_start_lineno - 1 :]
    body_content = "".join(body_lines).rstrip()

    # Strip old footers (any line containing footer emojis)
    body_content = _remove_footer_emojis(body_content)

    # Construct new file content
    final_content = _construct_file_content(header_first_line, docstring_str, body_content, footer)

    # Write back if changed
    try:
        if final_content != original_content:
            filepath.write_text(final_content, encoding="utf-8")
            return True
        return False
    except OSError as e:
        perr(f"Error writing {filepath}: {e}")
        return False


# --- Main Entry Point ---


def main(argv: list[str] | None = None) -> int:
    """Main entry point for pre-commit hook.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 = success, 1 = files modified/errors)
    """
    parser = argparse.ArgumentParser(
        description="Enforce SPDX headers and footer conformance (auto-detects repo)",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Python files to check (from pre-commit)",
    )
    parser.add_argument(
        "--footer",
        help="Override footer (for testing/manual use)",
    )

    args = parser.parse_args(argv)

    # Get footer (auto-detect unless overridden)
    if args.footer:
        footer = args.footer
    else:
        footer = get_footer_for_current_repo()
        repo_name = detect_repo_name()
        pout(f"Auto-detected repository: {repo_name}")
        pout(f"Using footer: {footer}")

    if not args.filenames:
        perr("No files specified")
        return 0

    # Process each file
    modified = False
    errors = False

    for filename in args.filenames:
        filepath = Path(filename)

        if not filepath.exists():
            perr(f"File not found: {filepath}")
            errors = True
            continue

        if filepath.suffix != ".py":
            continue  # Skip non-Python files

        try:
            was_modified = conform_file(filepath, footer)
            if was_modified:
                pout(f"✓ Fixed: {filepath}")
                modified = True
            else:
                pout(f"  OK: {filepath}")
        except Exception as e:
            perr(f"✗ Error processing {filepath}: {e}")
            errors = True

    # Exit code: 0 = no changes needed, 1 = files modified or errors
    if errors:
        return 1
    if modified:
        pout(f"\n{footer} Files modified - please review and re-add them")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

# 🧰⚙️🔚
