import pathlib
import warnings

from .check import check_source
from .formatter import format_source
from .sugar import SugarWarning, sugar

FORMATTER_DIR = pathlib.Path(__file__).parent / "formatter"


def get_formatter_pairs():
    pairs = []
    for input_file in sorted(FORMATTER_DIR.glob("*_input.sugar")):
        name = input_file.name.replace("_input.sugar", "")
        output_file = input_file.with_name(f"{name}_output.sugar")
        assert output_file.exists(), f"Missing output: {output_file}"
        pairs.append((name, input_file, output_file))
    return pairs


def test_formatter_fixtures():
    pairs = get_formatter_pairs()
    assert pairs, "No formatter pairs found"

    for name, input_file, output_file in pairs:
        source = input_file.read_text()
        expected = output_file.read_text()
        result = format_source(source)
        assert result == expected, (
            f"Formatter mismatch: {name}\nGOT:\n{result}\n\nEXPECTED:\n{expected}"
        )


def test_formatted_output_compiles_same():
    """Formatted code must produce identical HTML."""
    pairs = get_formatter_pairs()

    for name, input_file, _output_file in pairs:
        source = input_file.read_text()
        formatted = format_source(source)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SugarWarning)
            html_before = sugar(source)
            html_after = sugar(formatted)
        assert html_before == html_after, (
            f"Compilation changed after formatting: {name}"
        )


def test_formatted_snapshots():
    """All snapshot .sugar files should already be formatted."""
    snapshots_dir = pathlib.Path(__file__).parent / "snapshots"
    for sugar_file in sorted(snapshots_dir.glob("*.sugar")):
        source = sugar_file.read_text()
        formatted = format_source(source)
        assert source == formatted, (
            f"Snapshot not formatted: {sugar_file.name}\nRun format_source() on it."
        )


def test_format_is_idempotent():
    """Formatting twice should produce the same result."""
    pairs = get_formatter_pairs()

    for name, input_file, _output_file in pairs:
        source = input_file.read_text()
        once = format_source(source)
        twice = format_source(once)
        assert once == twice, f"Not idempotent: {name}"


def test_formatted_code_has_no_warnings():
    """Formatted code should produce zero warnings."""
    pairs = get_formatter_pairs()

    for name, _input_file, output_file in pairs:
        source = output_file.read_text()
        warnings = check_source(source)
        assert warnings == [], f"Warnings in formatted {name}:\n" + "\n".join(
            f"  line {w['line']}: {w['message']}" for w in warnings
        )
