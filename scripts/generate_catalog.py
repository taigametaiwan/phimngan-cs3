#!/usr/bin/env python3
"""Build a CloudStream repository index from the packaged CS3 manifests."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT / "addons"
ICONS = ROOT / "icons"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.cs3$")


def repository_from_git():
    try:
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    return f"{match.group(1)}/{match.group(2)}" if match else None


def read_addon(path, repository, branch):
    if not NAME_RE.fullmatch(path.name):
        raise ValueError(f"Invalid addon filename: {path.name}")
    try:
        with zipfile.ZipFile(path) as package:
            manifest = json.loads(package.read("manifest.json"))
            if "classes.dex" not in package.namelist():
                raise ValueError("missing classes.dex")
            icon = manifest.get("icon")
            if icon and icon not in package.namelist():
                raise ValueError(f"missing icon {icon}")
            icon_bytes = package.read(icon) if icon else None
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid CS3 package {path.name}: {exc}") from exc
    name = manifest.get("name")
    version = manifest.get("version")
    plugin_class = manifest.get("pluginClassName")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{path.name}: missing plugin name")
    if type(version) is not int or version < 0:
        raise ValueError(f"{path.name}: invalid version")
    if not isinstance(plugin_class, str) or not plugin_class.strip():
        raise ValueError(f"{path.name}: missing pluginClassName")
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = f"https://raw.githubusercontent.com/{repository}/{branch}"
    icon_url = manifest.get("iconUrl") or ""
    if icon_bytes:
        ICONS.mkdir(exist_ok=True)
        icon_path = ICONS / f"{path.stem}{Path(icon).suffix.lower()}"
        if not icon_path.exists() or icon_path.read_bytes() != icon_bytes:
            icon_path.write_bytes(icon_bytes)
        icon_url = f"{raw}/icons/{quote(icon_path.name)}"
    return {
        "iconUrl": icon_url,
        "fileHash": f"sha256-{file_hash}",
        "apiVersion": 1,
        "repositoryUrl": f"https://github.com/{repository}",
        "fileSize": path.stat().st_size,
        "status": 1,
        "authors": [],
        "tvTypes": ["Movie", "TvSeries"],
        "version": version,
        "internalName": path.stem,
        "description": f"Nguồn phim ngắn {name}",
        "url": f"{raw}/addons/{quote(path.name)}",
        "name": name,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", help="GitHub owner/repo; otherwise use GITHUB_REPOSITORY or origin")
    parser.add_argument("--branch", default=os.getenv("GITHUB_REF_NAME", "main"))
    parser.add_argument("--check", action="store_true", help="Fail if generated files differ")
    args = parser.parse_args()
    repository = args.repository or os.getenv("GITHUB_REPOSITORY") or repository_from_git()
    if not repository or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        parser.error("Pass --repository OWNER/REPO or configure GitHub origin")
    addons = sorted(ADDONS.glob("*.cs3"), key=lambda p: p.name.casefold())
    if not addons:
        parser.error("No .cs3 packages found in addons/")
    plugins = [read_addon(path, repository, args.branch) for path in addons]
    if len({p["internalName"].casefold() for p in plugins}) != len(plugins):
        parser.error("Duplicate addon filenames (case insensitive)")
    outputs = {
        ROOT / "repo.json": {
            "name": "PhimNgan CS3",
            "description": "Cổng addon phim ngắn CloudStream",
            "manifestVersion": 1,
            "pluginLists": [f"https://raw.githubusercontent.com/{repository}/{args.branch}/plugins.json"],
        },
        ROOT / "plugins.json": plugins,
    }
    stale = []
    for path, data in outputs.items():
        body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != body:
                stale.append(path.name)
        else:
            path.write_text(body, encoding="utf-8")
    if stale:
        print("Outdated: " + ", ".join(stale), file=sys.stderr)
        return 1
    print(f"Validated {len(plugins)} addons for {repository}@{args.branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
