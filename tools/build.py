#!/usr/bin/env python3
"""Package every folder in packages/ into a zip that is ready to share on awtrix.de.

Each package folder needs an awtrix.json manifest (see the repo README).

    python3 tools/build.py                          # validate all, zip all into dist/
    python3 tools/build.py --check                  # validate all, no zips
    python3 tools/build.py --tag big-clock-v1.2.0   # one package; fails if versions differ

Release tags are per package: <package-folder>-v<version>.

Standard library only, so it runs on any machine with Python 3.8+.
"""

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
    out = DIST / f"{pkg['folder'].name}-{pkg['version']}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in pkg["files"]:
            info = zipfile.ZipInfo(f"{pkg['folder'].name}/{name}", ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (pkg["folder"] / name).read_bytes())
    return out


def parse_tag(tag):
    """'big-clock-v1.2.0' -> ('big-clock', '1.2.0')"""
    m = re.match(r"^(.+)-v(\d[\w.\-]*)$", tag)
    if not m:
        raise PackageError(f"tag {tag!r} should look like <package-folder>-v<version>, "
                           f"for example big-clock-v1.2.0")
    return m.group(1), m.group(2)


def main():
    args = sys.argv[1:]
    check_only = "--check" in args
    tag = args[args.index("--tag") + 1] if "--tag" in args else None

    folders = sorted(p for p in PACKAGES.iterdir() if p.is_dir())
    want_version = None
    if tag:
        try:
            want_folder, want_version = parse_tag(tag)
        except PackageError as e:
            print(e, file=sys.stderr)
            return 1
        folders = [f for f in folders if f.name == want_folder]
        if not folders:
            print(f"tag {tag!r}: no folder packages/{want_folder}", file=sys.stderr)
            return 1

    packages, errors = [], []
    for folder in folders:
        if not (folder / "awtrix.json").is_file():
            errors.append(f"{folder.name}: missing awtrix.json")
            continue
        try:
            packages.append(load_package(folder))
        except PackageError as e:
            errors.append(f"{folder.name}: {e}")

    if want_version and packages and packages[0]["version"] != want_version:
        errors.append(f"{packages[0]['folder'].name}: tag says version {want_version} "
                      f"but the package says {packages[0]['version']}. Bump one to match.")

    if errors:
        print("Package problems:", *errors, sep="\n  ", file=sys.stderr)
        return 1

    for pkg in packages:
        print(f"ok  {pkg['folder'].name}  ({pkg['type']} {pkg['name']} {pkg['version']})")
    if check_only:
        return 0

    DIST.mkdir(exist_ok=True)
    for old in DIST.glob("*.zip"):
        old.unlink()
    for pkg in packages:
        print(f"->  {write_zip(pkg).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
