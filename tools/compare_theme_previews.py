"""Compare actual captures to immutable PNGs, with no pixel masks or threshold."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops


def changed_pixels(reference, actual):
    if reference.size != actual.size:
        raise ValueError("Different image size")
    bands = ImageChops.difference(reference.convert("RGBA"), actual.convert("RGBA")).split()
    maximum = bands[0]
    for band in bands[1:]:
        maximum = ImageChops.lighter(maximum, band)
    return reference.width * reference.height - maximum.histogram()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/theme-preview-diff"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reference_dir = root / "resources/themes/fluent2-v1/previews"
    if args.output.resolve().is_relative_to((root / "resources/themes/fluent2-v1").resolve()):
        raise ValueError("Comparison output must not overwrite the frozen resource directory")
    manifest = json.loads((reference_dir / "manifest.json").read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"pixel_threshold": 0, "masks": [], "files": [], "passed": True}
    for theme in manifest["themes"]:
        for record in [*theme["screens"], *theme["dialogs"]]:
            name = record["name"]
            source, actual = reference_dir / name, args.actual / name
            if hashlib.sha256(source.read_bytes()).hexdigest() != record["sha256"]:
                raise ValueError(f"Frozen reference changed: {name}")
            result = {"name": name, "passed": False}
            if not actual.exists():
                result["error"] = "Missing actual capture"
            else:
                with Image.open(source) as expected, Image.open(actual) as received:
                    if expected.size != received.size:
                        result["error"] = "Different image size"
                    else:
                        changed = changed_pixels(expected, received)
                        result.update(changed_pixels=changed, total_pixels=expected.width * expected.height, passed=changed == 0)
                        if changed:
                            ImageChops.difference(expected.convert("RGB"), received.convert("RGB")).save(args.output / name)
            report["files"].append(result)
            report["passed"] &= result["passed"]
    (args.output / "comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    failures = sum(not item["passed"] for item in report["files"])
    print(f"Compared {len(report['files'])} originals: {failures} differences/missing captures. Report: {args.output / 'comparison.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
