import difflib


def compute_diff(old_content: bytes, new_content: bytes) -> str:
    """Computes a unified text diff if possible, else returns binary placeholder."""
    try:
        old_text = old_content.decode("utf-8")
        new_text = new_content.decode("utf-8")
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="original",
            tofile="updated",
        )
        return "".join(diff)
    except UnicodeDecodeError:
        return "[Binary file modification - no text diff available]"
