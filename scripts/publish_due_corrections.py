#!/usr/bin/env python3
"""Decrypt corrections whose PSC release time has passed."""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def instant(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError(f"Timezone manquante: {value}")
    return result.astimezone(timezone.utc)

def repo_path(value: str) -> Path:
    result = (ROOT / value).resolve()
    if ROOT not in result.parents:
        raise ValueError(f"Chemin hors dépôt refusé: {value}")
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "publication/releases.json")
    parser.add_argument("--now", help="Date ISO-8601 (tests uniquement)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    now = instant(args.now) if args.now else datetime.now(timezone.utc)
    published: list[str] = []
    for release in manifest["releases"]:
        target, encrypted = repo_path(release["target"]), repo_path(release["encrypted"])
        if target.exists() or instant(release["release_at"]) > now:
            continue
        if not encrypted.is_file():
            raise FileNotFoundError(f"Archive chiffrée absente: {encrypted}")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["gpg", "--batch", "--yes", "--quiet", "--output", str(target), "--decrypt", str(encrypted)], check=True)
        published.append(release["target"])
    print(json.dumps({"now": now.isoformat(), "published": published}))
    if published and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write("published=true\nfiles=" + ",".join(published) + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
