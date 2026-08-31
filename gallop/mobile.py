"""One-way Markdown reading export. Never instantiate a mastery/backend writer."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
import time
import uuid

ROOTS = frozenset({
    "01-Mathematics", "02-Statistics-Econometrics", "03-Finance", "04-CS-AI",
    "05-Cross-Disciplinary", "Mathematics", "Statistics", "Finance", "CS-AI",
    "Practice", "Mistakes", "Papers", "Research", "Research Notes",
    "Gallop/Sessions", "Gallop/Practice/learner", "Gallop/Papers", "Gallop/Research",
})
DENIED = re.compile(
    r"(?:^|[^a-z0-9])(?:logs?|manifests?|integration[ _-]*tests?|configs?|configuration|"
    r"secrets?|oauth|tokens?|credentials?|passwords?|mastery(?:[ _-]*state)?|"
    r"backups?|backend|settings|cache|raw|data|schemas?|node_modules)(?:$|[^a-z0-9])", re.I
)
SENSITIVE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bBearer\s+\S+|"
    r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})\b|"
    r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|"
    r"[\"']?(?:api[ _-]?key|access[ _-]?token|refresh[ _-]?token|client[ _-]?secret|"
    r"password|passwd|authorization|private[ _-]?key|oauth[ _-]?token|api[ _-]?token)"
    r"[\"']?\s*[:=]\s*\S+|"
    r"[a-z]+://[^\s/@:]+:[^\s/@]+@", re.I
)
SYNTHETIC = re.compile(
    r"[\"']?integration[ _-]?test[\"']?\s*[:=]\s*[\"']?(?:true|yes|1)\b|"
    r"integration (?:acceptance evidence|test only)|__ACCEPTANCE_", re.I
)
PRIVATE = re.compile(r"[\"']?mobile_export[\"']?\s*[:=]\s*[\"']?(?:false|no|0)\b", re.I)
MAX_NOTE_BYTES = 5 * 1024 * 1024


class CloudNotReady(RuntimeError):
    """The provider has not acknowledged a directory; never pretend it has."""


def cloud_directory_ready(path: Path) -> bool:
    """Read Windows Cloud Files metadata; never change provider flags or DBs."""
    if os.name != "nt":
        raise ValueError("iCloud-safe directory checks require Windows")
    import ctypes as c
    from ctypes import wintypes as w
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p,
                                  w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    api = c.WinDLL("cldapi")
    api.CfGetPlaceholderInfo.argtypes = [w.HANDLE, c.c_int, c.c_void_p,
                                        w.DWORD, c.POINTER(w.DWORD)]
    api.CfGetPlaceholderInfo.restype = c.c_long
    handle = kernel.CreateFileW(str(path), 0x80, 7, None, 3, 0x02000000, None)
    if handle == c.c_void_p(-1).value:
        raise OSError(c.get_last_error(), "Cannot inspect cloud directory")
    try:
        buffer = c.create_string_buffer(65536)
        returned = w.DWORD()
        hr = api.CfGetPlaceholderInfo(handle, 0, buffer, len(buffer), c.byref(returned))
        if hr != 0:
            return False
        pin = c.c_uint32.from_buffer(buffer, 0).value
        in_sync = c.c_uint32.from_buffer(buffer, 4).value
        return pin != 3 and in_sync == 1
    finally:
        kernel.CloseHandle(handle)


def wait_cloud_directory(path: Path, *, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while not cloud_directory_ready(path):
        if time.monotonic() >= deadline:
            raise CloudNotReady(
                "iCloud has not acknowledged a Reader directory. Initialize the iCloud "
                "vault in iPhone Obsidian and resolve provider errors before retrying. "
                "No cloud state was forced and upload success is not confirmed."
            )
        time.sleep(min(1.0, max(0, deadline - time.monotonic())))


def hidden_or_system(path: Path) -> bool:
    return bool(getattr(path.stat(), "st_file_attributes", 0) & 0x6)


def cloud_safe_name(target: Path, name: str) -> None:
    """Conservative Windows/iCloud filename policy, checked before mutation."""
    rel = relative_file(name)
    if len(str(target / rel).encode("utf-16-le")) // 2 >= 256:
        raise ValueError("Mobile path exceeds the iCloud Windows path limit")
    for part in rel.parts:
        if (re.search(r'[<>:"/\\|?*\x00-\x1f]', part) or part.endswith((".", " "))
                or part.casefold().endswith((".nosync", ".tmp", ".icloud", ".download"))
                or re.match(r"^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)", part, re.I)):
            raise ValueError("Unsafe mobile filename")


def check_path(path: Path) -> Path:
    """Reject redirects, including ancestor junctions; cloud placeholders are OK."""
    path = path.absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Redirected filesystem path")
    return path.resolve()


def overlap(a: Path, b: Path) -> bool:
    return a == b or a in b.parents or b in a.parents


def relative_file(value: str) -> Path:
    p = Path(value)
    if p.is_absolute() or not p.parts or any(x in {".", ".."} or ":" in x for x in p.parts):
        raise ValueError("Invalid managed relative path")
    if any(x.startswith(".") for x in p.parts) or p.suffix.lower() != ".md":
        raise ValueError("Invalid managed file type")
    return p


def blocked_path(path: Path) -> bool:
    return any(part.startswith((".", "_")) or DENIED.search(part) for part in path.parts) or (
        any("deeptutor" in p.lower() for p in path.parts)
        and any("session" in p.lower() for p in path.parts)
    )


def collect(source: Path) -> tuple[dict[str, bytes], Counter]:
    notes: dict[str, bytes] = {}
    skipped: Counter = Counter()
    for root in sorted(ROOTS):
        base = source / root
        check_path(base)
        if not base.exists():
            continue
        if not base.is_dir():
            raise ValueError("Reading root must be a directory")
        if hidden_or_system(base):
            skipped["hidden_or_system"] += 1
            continue
        def on_error(error):
            raise error  # Never prune a mirror after an incomplete source scan.
        for folder, dirs, names in os.walk(base, followlinks=False, onerror=on_error):
            parent = Path(folder)
            for directory in list(dirs):
                child = parent / directory
                check_path(child)
                if blocked_path(child.relative_to(source)) or hidden_or_system(child):
                    dirs.remove(directory)
                    skipped["excluded_directory"] += 1
            for name in sorted(names):
                path = parent / name
                rel = path.relative_to(source)
                check_path(path)
                if blocked_path(rel) or path.suffix.lower() != ".md" or hidden_or_system(path):
                    skipped["path_or_type"] += 1
                    continue
                info = path.stat()
                if not path.is_file() or info.st_nlink != 1 or info.st_size > MAX_NOTE_BYTES:
                    skipped["size_or_link"] += 1
                    continue
                with path.open("rb") as stream:
                    payload = stream.read(MAX_NOTE_BYTES + 1)
                if len(payload) > MAX_NOTE_BYTES:
                    skipped["size_or_link"] += 1
                    continue
                try:
                    body = payload.decode("utf-8-sig")
                except UnicodeDecodeError:
                    skipped["encoding"] += 1
                    continue
                if "\x00" in body or SENSITIVE.search(body) or PRIVATE.search(body):
                    skipped["sensitive_or_private"] += 1
                elif SYNTHETIC.search(body):
                    skipped["synthetic"] += 1
                else:
                    notes[rel.as_posix()] = payload
    return notes, skipped


def atomic_bytes(path: Path, payload: bytes, *, staging_dir: Path | None = None,
                 create_only: bool = False) -> None:
    check_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    check_path(path)
    staging = check_path(staging_dir or path.parent)
    staging.mkdir(parents=True, exist_ok=True)
    if staging.stat().st_dev != path.parent.stat().st_dev:
        raise ValueError("Atomic export staging must be on the destination volume")
    fd, name = tempfile.mkstemp(prefix=".mobile-", dir=staging)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if create_only:
            # Windows rename refuses an existing target; never reuse its cloud object.
            if os.name == "nt":
                os.rename(name, path)
            else:
                # Atomic no-clobber publication; the staging link is removed below.
                os.link(name, path)
        else:
            os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def export_mobile(source: Path, target: Path, state: Path, *, dry_run: bool = False,
                  icloud_safe: bool = False, refresh: bool = False,
                  create_root_notes: bool = False, icloud_binding: Path | None = None,
                  automation_views: bool = False) -> dict:
    source, target, state = map(check_path, (source, target, state))
    if target.name != "Gallop-Reader":
        raise ValueError("Export target must be Gallop-Reader; retired vaults cannot be written")
    bound_identity = None
    def check_binding():
        if __package__:
            from .mobile_icloud import validate_target
        else:
            from mobile_icloud import validate_target
        try:
            return validate_target(target, check_path(icloud_binding))
        except (ValueError, OSError, KeyError) as exc:
            raise CloudNotReady(f'iCloud identity validation stopped export: {exc}') from exc
    if icloud_binding is not None:
        bound_identity = check_binding()
        icloud_safe = True
    if not source.is_dir() or not (source / ".obsidian").is_dir():
        raise ValueError("Source must be an existing Obsidian vault")
    if any(overlap(a, b) for a, b in (
        (source, target), (source, state), (target, state)
    )):
        raise ValueError("Source, mobile vault and local export state must be separate")
    # State is local metadata and conflict backups; never place it in a cloud vault.
    receipt = state / "receipt.json"
    check_path(receipt)
    check_path(target / ".obsidian")
    prior = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
    identity = {"source": str(source), "target": str(target)}
    if prior and prior.get('icloud_target') and prior['icloud_target'] != bound_identity:
        raise CloudNotReady('The receipt belongs to another iCloud object; explicit rebind is required')
    if prior and any(prior.get(k) != v for k, v in identity.items()):
        raise ValueError("Export state belongs to a different vault pair")
    if bound_identity:
        identity['icloud_target'] = bound_identity
    if prior is None and target.exists() and any(p.name != ".obsidian" for p in target.iterdir()):
        raise ValueError("Initial target must be empty (except mobile Obsidian settings)")
    owned = set(prior["files"]) if prior else set()
    for name in owned:
        relative_file(name)
        check_path(target / name)
    notes, skipped = collect(source)
    automation_today = None
    if automation_views or (source / "Gallop/Automation/Today.md").is_file():
        if not __package__:
            # The existing launcher executes this file directly, outside package mode.
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from gallop.automation.views import collect_views
        views = collect_views(source)
        automation_today = views.get("Gallop/Automation/Today.md")
        notes.update(views)
    date = datetime.now().astimezone().date().isoformat()
    links = [f"- [[{Path(n).with_suffix('').as_posix()}]]" for n in sorted(notes)
             if not any(c in n for c in "[]#|^\r\n")]
    notes["Today.md"] = (f"# {target.name}\n\n阅读镜像日期：{date}\n\n"
        "> 仅供阅读。内容来自电脑主 Vault；手机修改不会写回，下一次导出以主 Vault 为准。\n\n"
        "本页是阅读索引，不推断今日复习任务或掌握度。集成测试不作为学习记录。\n\n"
        f"## 阅读笔记（{len(notes)}）\n\n" + "\n".join(links) +
        "\n\n[[Mobile Sync Check|同步检查]]\n").encode("utf-8")
    notes["Mobile Sync Check.md"] = (
        "# 手机同步检查\n\n这是安全的同步样例，不是课程成绩或掌握度证据。\n\n"
        f"如果你在 iPhone Obsidian 的 {target.name} 中看到此页，阅读通道已到达手机。\n\n"
        "样例：1 + 1 = 2。\n").encode("utf-8")
    if automation_today is not None:
        notes["Today.md"] = automation_today
    if create_root_notes:
        if not target.is_dir():
            raise ValueError("Root-note repair requires the existing Reader vault")
        notes = {name: notes[name] for name in ("Today.md", "Mobile Sync Check.md")}
        if any((target / name).exists() for name in notes):
            raise FileExistsError("Back up and remove the two old mirrors; wait for cloud deletion first")
    for name in notes:
        cloud_safe_name(target, name)
        check_path(target / name)
    result = {"reading_notes": len(notes) - 2, "generated_notes": 2,
              "skipped": dict(skipped), "written": 0, "unchanged": 0,
              "quarantined": 0, "removed_empty_settings": 0, "dry_run": dry_run}
    if dry_run:
        return result
    state.mkdir(parents=True, exist_ok=True)
    lock = state / "export.lock"
    check_path(lock)
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        # Refuse if another completed exporter changed ownership during the scan.
        current = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
        if current != prior:
            raise RuntimeError("Export state changed during scan; retry")
        if icloud_binding is not None and check_binding() != bound_identity:
            raise CloudNotReady('iCloud identity changed during source scan')
        target.mkdir(parents=True, exist_ok=True)
        # A phone creates its own settings. Retire only the empty legacy directory.
        settings = check_path(target / ".obsidian")
        if not create_root_notes and settings.is_dir() and not any(settings.iterdir()):
            settings.rmdir()
            result["removed_empty_settings"] += 1
        staging = state / "staging"
        staging.mkdir(exist_ok=True)
        if staging.stat().st_dev != target.stat().st_dev:
            raise ValueError("Keep local state outside iCloud but on the Reader volume")
        if icloud_safe:
            wait_cloud_directory(target)
            # Establish parents before submitting children, avoiding orphan uploads.
            folders = {parent for name in notes for parent in (target / name).parents
                       if target in parent.parents}
            for folder in sorted(folders, key=lambda p: (len(p.parts), str(p))):
                folder.mkdir(exist_ok=True)
                wait_cloud_directory(folder)
        backup = state / "backups" / uuid.uuid4().hex
        # Persist intended ownership first so interrupted writes are replayable.
        atomic_bytes(receipt, json.dumps({**identity, "files": sorted(owned | notes.keys())}).encode())
        for name, payload in sorted(notes.items()):
            dest = check_path(target / name)
            if create_root_notes and dest.exists():
                raise FileExistsError("A root note reappeared during repair; no overwrite allowed")
            if dest.exists():
                old = dest.read_bytes()
                if old == payload and not refresh:
                    result["unchanged"] += 1
                    continue
                atomic_bytes(backup / name, old)
            atomic_bytes(dest, payload, staging_dir=staging, create_only=create_root_notes)
            result["written"] += 1
        # Retire only previously owned exports. No source or unknown file is deleted.
        for name in sorted(owned - notes.keys()) if not create_root_notes else []:
            dest = check_path(target / name)
            if dest.exists():
                atomic_bytes(backup / name, dest.read_bytes())
                dest.unlink()
                result["quarantined"] += 1
        final_owned = owned | notes.keys() if create_root_notes else notes.keys()
        atomic_bytes(receipt, json.dumps({**identity, "files": sorted(final_owned)}).encode())
    finally:
        lock.unlink()
    return result


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True,
                        help="Local receipt/backups directory outside both vaults and cloud storage")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--icloud-safe", action="store_true",
                        help="Wait for Windows iCloud to acknowledge parent folders")
    parser.add_argument('--icloud-binding', type=Path,
                        help='Local binding JSON: validate live provider, object and parent before export')
    parser.add_argument("--refresh", action="store_true",
                        help="Back up and republish owned reading files, even if identical")
    parser.add_argument("--create-root-notes", action="store_true",
                        help="Only create missing Today.md and Mobile Sync Check.md as fresh objects")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_arguments(parser)
    args = parser.parse_args()
    try:
        print(json.dumps(export_mobile(args.source, args.target, args.state, dry_run=args.dry_run,
                                       icloud_safe=args.icloud_safe, refresh=args.refresh,
                                       create_root_notes=args.create_root_notes,
                                       icloud_binding=args.icloud_binding)))
        return 0
    except CloudNotReady as exc:
        print(str(exc))
        return 2
    except Exception as exc:
        print(f"Mobile export stopped: {type(exc).__name__}. No backend writes were requested.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
