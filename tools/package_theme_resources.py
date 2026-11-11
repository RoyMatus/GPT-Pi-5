"""Export the frozen preview implementation; never install or modify an application."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

RESOURCE = Path("resources/themes/fluent2-v1")


def safe_name(name):
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe resource path: {name}")
    return name


def checked_bytes(file, expected):
    data = file.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Checksum mismatch: {file.name}")
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)
    return result.stdout


def write_archive(output, entries):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(safe_name(name), date_time=(2026, 11, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def collect_entries(root):
    directory = root / RESOURCE
    lock_bytes = (directory / "resource-lock.json").read_bytes()
    lock = json.loads(lock_bytes)
    entries = {"resource-lock.json": lock_bytes}
    for record in lock["source_files"]:
        name = safe_name(record["path"])
        try:
            data = git_bytes(root, "show", f"{lock['source_commit']}:{name}")
        except (subprocess.CalledProcessError, OSError):
            # GitHub source ZIPs lack .git; only exact locked file bytes may substitute.
            data = checked_bytes(root / name, record["sha256"])
        if digest(data) != record["sha256"]:
            raise ValueError(f"Source checksum mismatch: {name}")
        entries["source/" + name] = data
    for record in lock["preview_files"]:
        name = safe_name(record["path"])
        entries[name] = checked_bytes(directory / name, record["sha256"])
    for record in lock["runtime_files"]:
        name = safe_name(record["path"])
        entries["runtime/" + name.removeprefix("src/")] = checked_bytes(root / name, record["sha256"])
    patch = checked_bytes(directory / "integration.patch", lock["integration_patch_sha256"])
    entries["integration.patch"] = patch
    for name in ("README.md", "DESIGN_LOCK.md", "SOL-6.1-PROMPT.md"):
        entries[name] = (directory / name).read_bytes()
    for name in ("tests/browser-theme-responsive.mjs", "tools/package_theme_resources.py", "tools/compare_theme_previews.py", "tests/test_theme_resources.py", "tests/test_theme_preview_comparison.py"):
        entries["validation/" + name] = (root / name).read_bytes()
    for record in lock["audit_files"]:
        name = safe_name(record["path"])
        entries[name] = checked_bytes(directory / name, record["sha256"])
    manifest = {"schema": 1, "resource_id": lock["resource_id"], "source_commit": lock["source_commit"],
                "base_commit": lock["base_commit"], "files": [
                    {"path": name, "bytes": len(data), "sha256": digest(data)}
                    for name, data in sorted(entries.items())]}
    entries["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    return entries, lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/GPT-Pi-5-theme-resources-v1.zip"))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    entries, lock = collect_entries(root)
    summary = {"resource_id": lock["resource_id"], "source_commit": lock["source_commit"], "verified_files": len(entries) - 1}
    if not args.verify_only:
        output = args.output if args.output.is_absolute() else root / args.output
        if output.suffix != ".zip" or output.resolve().is_relative_to((root / RESOURCE).resolve()):
            raise ValueError("Output must be a ZIP outside the frozen resource directory")
        write_archive(output, entries)
        with zipfile.ZipFile(output) as archive:
            for name, data in entries.items():
                if archive.read(name) != data:
                    raise ValueError(f"Archive verification failed: {name}")
        summary.update(archive=str(output), bytes=output.stat().st_size, sha256=digest(output.read_bytes()))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
