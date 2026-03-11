"""TOON (Token-Oriented Object Notation) encoder for efficient LLM context usage.

This implements a TOON-like compression that reduces token count by 30-60%
compared to JSON by:
- Using YAML-like indentation for nested objects
- Using CSV-like tabular format for arrays of uniform objects
- Removing unnecessary punctuation (braces, brackets, quotes)
- Only quoting strings when absolutely necessary

Pure Python implementation with no external dependencies.
"""

import re
from typing import Any


def _needs_quoting(value: str) -> bool:
    """Determine if a string value needs to be quoted."""
    if not value:
        return True
    # Quote if contains keywords, numbers, delimiters, or special chars
    keywords = {'true', 'false', 'null', 'none'}
    if value.lower() in keywords:
        return True
    # Quote if it looks like a number
    try:
        float(value)
        return True
    except ValueError:
        pass
    # Quote if contains delimiter, newline, or structural chars
    if re.search(r'[,|\t\n:{}\[\]]', value):
        return True
    # Quote if starts with space or special chars
    if value[0] in ' \t#':
        return True
    # Quote if empty or whitespace
    if not value.strip():
        return True
    return False


def _format_value(value: Any, delimiter: str = ",") -> str:
    """Format a single value for TOON output."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        # Format numbers nicely
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, str):
        if _needs_quoting(value):
            # Escape quotes and backslashes
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        return value
    return str(value)


def _is_uniform_array(arr: list) -> bool:
    """Check if array contains uniform objects (same keys)."""
    if not arr:
        return False
    if not all(isinstance(item, dict) for item in arr):
        return False
    if len(arr) == 1:
        return True
    # Check if all dicts have the same keys
    keys = set(arr[0].keys())
    return all(set(item.keys()) == keys for item in arr)


def _encode_object(obj: dict, indent: int = 0, indent_size: int = 2, delimiter: str = ",") -> str:
    """Encode a dictionary object using YAML-like indentation."""
    lines = []
    prefix = " " * indent

    for key, value in obj.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_encode_object(value, indent + indent_size, indent_size, delimiter))
        elif isinstance(value, list):
            if _is_uniform_array(value) and len(value) > 0:
                # Use tabular format for uniform arrays
                lines.append(_encode_tabular_array(key, value, indent, indent_size, delimiter))
            else:
                # Use itemized format for non-uniform arrays
                lines.append(f"{prefix}{key}:")
                lines.append(_encode_array(value, indent + indent_size, indent_size, delimiter))
        else:
            lines.append(f"{prefix}{key}: {_format_value(value, delimiter)}")

    return "\n".join(lines)


def _encode_tabular_array(key: str, arr: list, indent: int, indent_size: int, delimiter: str) -> str:
    """Encode a uniform array as a CSV-like table."""
    prefix = " " * indent
    n = len(arr)
    keys = list(arr[0].keys())

    # Header: [N,]{keys}:
    keys_str = delimiter.join(keys)
    header = f"{prefix}[{n},]{{{keys_str}}}:"

    # Rows
    rows = []
    for item in arr:
        values = []
        for k in keys:
            val = item.get(k)
            values.append(_format_value(val, delimiter))
        rows.append(prefix + delimiter.join(values))

    return header + "\n" + "\n".join(rows)


def _encode_array(arr: list, indent: int = 0, indent_size: int = 2, delimiter: str = ",") -> str:
    """Encode a non-uniform array using itemized format."""
    lines = []
    prefix = " " * indent

    for i, item in enumerate(arr):
        if isinstance(item, dict):
            lines.append(f"{prefix}-")
            obj_lines = _encode_object(item, indent + indent_size, indent_size, delimiter)
            lines.append(obj_lines)
        elif isinstance(item, list):
            lines.append(f"{prefix}-")
            lines.append(_encode_array(item, indent + indent_size, indent_size, delimiter))
        else:
            lines.append(f"{prefix}- {_format_value(item, delimiter)}")

    return "\n".join(lines)


def encode(value: Any, options: dict = None) -> str:
    """
    Encode a Python value to TOON format for efficient LLM context usage.

    Args:
        value: The Python value to encode (dict, list, or primitive)
        options: Optional configuration dict with:
            - delimiter: "," (default), "\t", or "|" for field separation
            - indent: Spaces per indent level (default: 2)
            - lengthMarker: "#" to prefix array lengths (default: "")

    Returns:
        TOON-formatted string

    Examples:
        >>> encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'

        >>> encode([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        '[2,]{id,name}:\\n1,Alice\\n2,Bob'
    """
    options = options or {}
    delimiter = options.get("delimiter", ",")
    indent_size = options.get("indent", 2)
    length_marker = options.get("lengthMarker", "")

    if isinstance(value, dict):
        return _encode_object(value, 0, indent_size, delimiter)
    elif isinstance(value, list):
        if _is_uniform_array(value) and len(value) > 0:
            # For top-level uniform array, create a synthetic key
            keys = list(value[0].keys())
            n = len(value)
            keys_str = delimiter.join(keys)

            if length_marker:
                header = f"#[{n}]{{{keys_str}}}:"
            else:
                header = f"[{n},]{{{keys_str}}}:"

            rows = []
            for item in value:
                values = []
                for k in keys:
                    val = item.get(k)
                    values.append(_format_value(val, delimiter))
                rows.append(delimiter.join(values))

            return header + "\n" + "\n".join(rows)
        else:
            return _encode_array(value, 0, indent_size, delimiter)
    else:
        return _format_value(value, delimiter)


def encode_compact(value: Any) -> str:
    """
    Encode a value in the most compact TOON format.
    Uses minimal indentation and tab delimiter for maximum compression.
    """
    return encode(value, {"delimiter": "\t", "indent": 1})


def estimate_token_savings(json_str: str, toon_str: str) -> dict:
    """
    Estimate the token savings when using TOON vs JSON.
    Returns stats about character and estimated token reduction.
    """
    json_len = len(json_str)
    toon_len = len(toon_str)

    # Rough estimate: ~4 chars per token on average
    json_tokens = json_len // 4
    toon_tokens = toon_len // 4

    char_savings = json_len - toon_len
    token_savings = json_tokens - toon_tokens
    percent_reduction = (char_savings / json_len * 100) if json_len > 0 else 0

    return {
        "json_chars": json_len,
        "toon_chars": toon_len,
        "char_savings": char_savings,
        "estimated_json_tokens": json_tokens,
        "estimated_toon_tokens": toon_tokens,
        "token_savings": token_savings,
        "percent_reduction": round(percent_reduction, 1)
    }


# Convenience function to wrap tool outputs
def compress_output(data: Any, compact: bool = True) -> str:
    """
    Compress tool output data to TOON format.
    Use this for MCP tool responses to reduce context window usage.

    Args:
        data: Python value to compress
        compact: Use compact format (tab delimiter, minimal indent)

    Returns:
        TOON-formatted string
    """
    if compact:
        return encode_compact(data)
    return encode(data)