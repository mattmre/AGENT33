"""Check pinned upstream runtime protocol sources for compatibility drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

LOCKFILE_PATH = Path(__file__).resolve().parents[1] / "runtime_compatibility.lock.json"


def _normalize_text(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8", "ignore").replace("\r\n", "\n")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_lockfile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_source(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return _normalize_text(response.read())


def _validate_required_substrings(
    *,
    source_id: str,
    text: str,
    required_substrings: list[str],
) -> None:
    missing = [needle for needle in required_substrings if needle not in text]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"{source_id}: missing required upstream markers: {joined}")


def _refresh_lock(lockfile: dict[str, Any]) -> dict[str, Any]:
    refreshed = json.loads(json.dumps(lockfile))
    for source in refreshed["sources"]:
        text = _fetch_source(source["url"])
        _validate_required_substrings(
            source_id=source["id"],
            text=text,
            required_substrings=list(source.get("required_substrings", [])),
        )
        source["sha256"] = _sha256_text(text)
    return refreshed


def _check_lock(lockfile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for source in lockfile["sources"]:
        text = _fetch_source(source["url"])
        _validate_required_substrings(
            source_id=source["id"],
            text=text,
            required_substrings=list(source.get("required_substrings", [])),
        )
        actual_hash = _sha256_text(text)
        expected_hash = source.get("sha256", "")
        if actual_hash != expected_hash:
            errors.append(
                f"{source['id']}: upstream compatibility source drifted\n"
                f"  url: {source['url']}\n"
                f"  expected: {expected_hash}\n"
                f"  actual:   {actual_hash}\n"
                "  refresh with: python scripts/check_runtime_compatibility.py --write-lock"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-lock",
        action="store_true",
        help="Refresh runtime_compatibility.lock.json to the current upstream hashes.",
    )
    args = parser.parse_args()

    lockfile = _load_lockfile(LOCKFILE_PATH)
    if args.write_lock:
        refreshed = _refresh_lock(lockfile)
        LOCKFILE_PATH.write_text(
            json.dumps(refreshed, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"updated {LOCKFILE_PATH}")
        return 0

    errors = _check_lock(lockfile)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("runtime compatibility lock is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
