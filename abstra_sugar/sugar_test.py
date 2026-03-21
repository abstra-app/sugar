import json
import pathlib

from .sugar import sugar

SNAPSHOTS_DIR = pathlib.Path(__file__).parent / "snapshots"


def get_snapshot_pairs():
    pairs = []
    for sugar_file in sorted(SNAPSHOTS_DIR.glob("*.sugar")):
        html_file = sugar_file.with_suffix(".html")
        json_file = sugar_file.with_suffix(".json")
        assert html_file.exists(), f"Missing snapshot: {html_file}"
        data = json.loads(json_file.read_text()) if json_file.exists() else None
        pairs.append((sugar_file, html_file, data))
    return pairs


def test_snapshots():
    pairs = get_snapshot_pairs()
    assert pairs, "No snapshot pairs found"

    for sugar_file, html_file, data in pairs:
        source = sugar_file.read_text()
        expected = html_file.read_text()
        result = sugar(source, data)
        assert result == expected, f"Snapshot mismatch: {sugar_file.name}"
