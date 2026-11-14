#!/usr/bin/env python3
"""Package every folder in packages/ into a zip that is ready to share on awtrix.de.

Each package folder needs an awtrix.json manifest (see the repo README).

    python3 tools/build.py                                   # zip every package into dist/
    python3 tools/build.py packages/big-clock --tag v1.0     # zip one package as dist/big-clock-v1.0.zip
    python3 tools/build.py --check                           # validate only

--tag must match the package's version (for a script, its '# @version' line).

Standard library only, so it runs on any machine with Python 3.8+.
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ROOT / "packages"
DIST = ROOT / "dist"

TYPES = ("script", "flow", "icon")
# Fixed timestamp so the same files always give the same zip.
ZIP_DATE = (2020, 1, 1, 0, 0, 0)
HEADER_LINE = re.compile(r"^#\s*@(\w+)\s+(.*?)\s*$")


class PackageError(Exception):
    pass


def read_script_header(path):
    """Read the '# @key value' block at the top of an .ax script."""
    header = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        m = HEADER_LINE.match(line)
        if m and m.group(1) != "config":
            header[m.group(1)] = m.group(2)
    return header


def load_package(folder):
    """Validate one package folder and return what the build needs."""
    manifest_path = folder / "awtrix.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PackageError(f"awtrix.json is not valid JSON: {e}")

    kind = manifest.get("type")
    if kind not in TYPES:
        raise PackageError(f"'type' must be one of {', '.join(TYPES)} (got {kind!r})")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise PackageError("'files' must be a non-empty list of file names")

    preview = manifest.get("preview")
    extras = ["README.md"] + ([preview] if preview else [])
    for name in files + extras:
        if not (folder / name).is_file():
            raise PackageError(f"file not found: {name}")

    if kind == "script":
        scripts = [f for f in files if f.endswith(".ax")]
        if len(scripts) != 1:
            raise PackageError("a script package needs exactly one .ax file in 'files'")
        header = read_script_header(folder / scripts[0])
        for key in ("name", "version"):
            if key in manifest:
                raise PackageError(f"don't set '{key}' in awtrix.json for scripts; "
                                   f"it comes from '# @{key}' in {scripts[0]}")
            if key not in header:
                raise PackageError(f"{scripts[0]} is missing its '# @{key}' header line")
        name, version = header["name"], header["version"]
    else:
        name, version = manifest.get("name"), manifest.get("version")
        if not name or not version:
            raise PackageError(f"a {kind} package needs 'name' and 'version' in awtrix.json")

    return {
        "folder": folder,
        "type": kind,
        "name": name,
        "version": str(version),
        "files": list(dict.fromkeys(files + extras)),
    }


def write_zip(pkg):
    out = DIST / f"{pkg['folder'].name}-v{pkg['version']}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in pkg["files"]:
            info = zipfile.ZipInfo(f"{pkg['folder'].name}/{name}", ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (pkg["folder"] / name).read_bytes())
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Validate packages and zip them into dist/ for sharing on awtrix.de.")
    parser.add_argument("dirs", nargs="*", type=Path, metavar="DIR",
                        help="package folder(s) to build (default: every folder in packages/)")
    parser.add_argument("--tag", help="release tag such as v1.0; must match the package's version")
    parser.add_argument("--check", action="store_true", help="validate only, don't write zips")
    args = parser.parse_args()

    want_version = args.tag[1:] if args.tag and args.tag[0] in "vV" else args.tag
    folders = [d.resolve() for d in args.dirs] or sorted(p for p in PACKAGES.iterdir() if p.is_dir())

    packages, errors = [], []
    for folder in folders:
        if not folder.is_dir():
            errors.append(f"{folder}: not a directory")
        elif not (folder / "awtrix.json").is_file():
            errors.append(f"{folder.name}: missing awtrix.json")
        else:
            try:
                pkg = load_package(folder)
            except PackageError as e:
                errors.append(f"{folder.name}: {e}")
                continue
            if want_version and pkg["version"] != want_version:
                errors.append(f"{folder.name}: tag {args.tag} doesn't match the package's version "
                              f"{pkg['version']}. Bump one to match.")
            packages.append(pkg)

    if errors:
        print("Package problems:", *errors, sep="\n  ", file=sys.stderr)
        return 1

    for pkg in packages:
        print(f"ok  {pkg['folder'].name}  ({pkg['type']} {pkg['name']} {pkg['version']})")
    if args.check:
        return 0

    DIST.mkdir(exist_ok=True)
    for pkg in packages:
        print(f"->  {write_zip(pkg).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
