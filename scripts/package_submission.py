"""Create a deterministic ZIP of the source, report, and reproducible evidence."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ["code", "configs", "experiments/pilot_3000", "results", "report", "scripts"]
INCLUDE_FILES = ["README.md", "requirements.txt", "requirements-lock.txt", "docs/data-dictionary.md", "docs/learning-guide.md", "docs/verification.json", "docs/browser-verification.json"]


def main():
    if not (ROOT / "report/index.html").is_file():
        raise SystemExit("Build and verify the report before packaging")
    paths = [ROOT / name for name in INCLUDE_FILES if (ROOT / name).is_file()]
    for name in INCLUDE_DIRS:
        paths.extend(path for path in (ROOT / name).rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")
    paths = sorted(set(paths))
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    manifest = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    archive_path = dist / "Chenglong_Zhang_50068179_IOTA_Qlearning.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            info = zipfile.ZipInfo("IOTA-RL/" + str(path.relative_to(ROOT)), date_time=(2026,10,24,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("IOTA-RL/SUBMISSION_SHA256.json", date_time=(2026,10,24,0,0,0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, manifest_bytes)
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        for relative, expected in manifest.items():
            assert hashlib.sha256(archive.read("IOTA-RL/" + relative)).hexdigest() == expected
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (dist / "SHA256SUMS").write_text(f"{digest}  {archive_path.name}\n")
    print(f"Created {archive_path.name}: {len(paths)} files plus SHA-256 manifest; {archive_path.stat().st_size/1e6:.2f} MB")
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
