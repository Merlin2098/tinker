#!/usr/bin/env python3
"""
Invoker installer (portable deployment helper).

Copies the Invoker framework footprint into one or more destination projects and
merges host-facing files:
- requirements.txt: add missing deps (do not remove)
- .gitignore: add missing lines from instructions/model_agnostic/.gitignore.host

This tool is intentionally conservative:
- By default it does not overwrite existing framework files (only merges).
- Use --overwrite-framework to overwrite and optionally --backup.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


def invoker_root() -> Path:
    return Path(__file__).resolve().parent


def now_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_line(line: str) -> str:
    return line.rstrip("\r\n")


def is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#")


_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)")


def requirement_name(line: str) -> Optional[str]:
    """
    Best-effort extraction of a package name from a requirements.txt line.
    Returns None for directives and non-standard entries.
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    if s.startswith(("-", "--")):
        # -r, -c, -e, --find-links, etc.
        return None
    m = _REQ_NAME_RE.match(s)
    if not m:
        return None
    return m.group(1).lower().replace("_", "-")


def strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
        return s[1:-1].strip()
    return s


def normalize_windows_long_path(path_str: str) -> str:
    """
    Best-effort support for very long Windows paths by applying the \\?\\ prefix
    to absolute paths when needed.
    """
    s = strip_quotes(path_str)
    if os.name != "nt":
        return s
    if s.startswith("\\\\?\\"):
        return s
    if s.startswith("\\\\"):
        # UNC path: \\server\share\...
        return "\\\\?\\UNC\\" + s.lstrip("\\")
    if re.match(r"^[A-Za-z]:\\", s):
        # Drive absolute: C:\...
        return "\\\\?\\" + s
    return s


def resolve_dest_root(dest_str: str) -> Path:
    raw = strip_quotes(dest_str)
    p = Path(raw).expanduser()
    try:
        abs_p = p.resolve()
    except Exception:
        abs_p = p.absolute()

    abs_str = str(abs_p)
    # Apply long-path prefix only when it's likely to matter.
    if os.name == "nt" and len(abs_str) >= 240:
        return Path(normalize_windows_long_path(abs_str))
    return abs_p


@dataclass
class ChangeReport:
    copied: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)
    backups: list[str] = field(default_factory=list)
    requirements_added: list[str] = field(default_factory=list)
    gitignore_added: int = 0
    legacy_found: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def backup_file(dest_root: Path, target: Path, backup_root: Path, report: ChangeReport) -> None:
    rel = target.relative_to(dest_root)
    bpath = backup_root / rel
    bpath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, bpath)
    report.backups.append(str(bpath))


def copy_file(
    src: Path,
    dest_root: Path,
    dest: Path,
    *,
    overwrite: bool,
    backup_root: Optional[Path],
    dry_run: bool,
    report: ChangeReport,
) -> None:
    if dest.exists():
        if not overwrite:
            report.skipped_existing.append(str(dest))
            return
        if backup_root is not None and not dry_run:
            backup_file(dest_root, dest, backup_root, report)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        report.overwritten.append(str(dest))
        return

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    report.copied.append(str(dest))


def copy_tree(
    src_dir: Path,
    dest_dir: Path,
    dest_root: Path,
    *,
    overwrite: bool,
    backup_root: Optional[Path],
    dry_run: bool,
    report: ChangeReport,
) -> None:
    for root, _dirs, files in os.walk(src_dir):
        root_path = Path(root)
        for fname in files:
            src = root_path / fname
            rel = src.relative_to(src_dir)
            dest = dest_dir / rel
            copy_file(
                src,
                dest_root,
                dest,
                overwrite=overwrite,
                backup_root=backup_root,
                dry_run=dry_run,
                report=report,
            )


def merge_gitignore(
    invoker_gitignore_host: Path,
    dest_gitignore: Path,
    *,
    dry_run: bool,
    report: ChangeReport,
) -> None:
    host_lines = [normalize_line(l) for l in read_text(invoker_gitignore_host).splitlines()]
    if dest_gitignore.exists():
        dest_lines = [normalize_line(l) for l in read_text(dest_gitignore).splitlines()]
    else:
        dest_lines = []

    existing = {l.strip() for l in dest_lines if l.strip()}
    to_add = [l for l in host_lines if l.strip() and l.strip() not in existing]
    if not to_add:
        return

    out_lines = list(dest_lines)
    if out_lines and out_lines[-1].strip():
        out_lines.append("")
    out_lines.extend(to_add)

    if not dry_run:
        write_text(dest_gitignore, "\n".join(out_lines) + "\n")
    report.gitignore_added += len(to_add)


def merge_requirements(
    invoker_reqs: Path,
    dest_reqs: Path,
    *,
    dry_run: bool,
    report: ChangeReport,
) -> None:
    inv_lines = [normalize_line(l) for l in read_text(invoker_reqs).splitlines()]
    inv_entries = [l for l in inv_lines if not is_blank_or_comment(l)]
    inv_by_name: dict[str, str] = {}
    inv_other: list[str] = []
    for line in inv_entries:
        name = requirement_name(line)
        if name is None:
            inv_other.append(line.strip())
        else:
            inv_by_name.setdefault(name, line.strip())

    if not dest_reqs.exists():
        content = "\n".join(inv_lines).rstrip() + "\n"
        if not dry_run:
            write_text(dest_reqs, content)
        report.requirements_added.extend([l for l in inv_entries if l.strip()])
        return

    dest_lines = [normalize_line(l) for l in read_text(dest_reqs).splitlines()]
    dest_entries = [l for l in dest_lines if not is_blank_or_comment(l)]
    dest_names = {n for n in (requirement_name(l) for l in dest_entries) if n}
    dest_exact = {l.strip() for l in dest_entries}

    missing: list[str] = []
    for name, line in inv_by_name.items():
        if name not in dest_names:
            missing.append(line)
    for line in inv_other:
        if line and line not in dest_exact:
            missing.append(line)

    if not missing:
        return

    out_lines = list(dest_lines)
    if out_lines and out_lines[-1].strip():
        out_lines.append("")
    out_lines.append("# Added by Invoker installer (missing deps)")
    out_lines.extend(missing)

    if not dry_run:
        write_text(dest_reqs, "\n".join(out_lines) + "\n")
    report.requirements_added.extend(missing)


def detect_legacy(dest_root: Path, report: ChangeReport) -> None:
    legacy_paths = [
        dest_root / "instructions" / "trigger_vscode.md",
        dest_root / "instructions" / "trigger_antigravity.md",
        dest_root / "instructions" / "trigger_generic.md",
        dest_root / "instructions" / "trigger_chat.md",
        dest_root / "instructions" / "command_glossary_chat.md",
    ]
    for p in legacy_paths:
        if p.exists():
            report.legacy_found.append(str(p))


def migrate_legacy(
    dest_root: Path,
    *,
    backup_root: Optional[Path],
    dry_run: bool,
    report: ChangeReport,
) -> None:
    if not report.legacy_found:
        return
    legacy_dir = dest_root / "instructions" / "legacy"
    for p_str in list(report.legacy_found):
        p = Path(p_str)
        if not p.exists():
            continue
        target = legacy_dir / p.name
        if backup_root is not None and not dry_run:
            backup_file(dest_root, p, backup_root, report)
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(target))
        report.warnings.append(f"Moved legacy file to: {target}")


def framework_items() -> list[Path]:
    root = invoker_root()
    candidates = [
        root / "agent",
        root / "agent_tools",
        root / "instructions",
        root / ".clinerules",
        root / "agent_framework_config.yaml",
        root / "AGENTS.md",
        root / "agent.md",
    ]
    return [p for p in candidates if p.exists()]


def print_report(dest: Path, report: ChangeReport) -> None:
    print(f"\n== Invoker install report: {dest} ==")
    if report.legacy_found:
        print(f"Legacy found: {len(report.legacy_found)}")
        for p in report.legacy_found[:10]:
            print(f"  - {p}")
        if len(report.legacy_found) > 10:
            print("  - ...")
    if report.copied:
        print(f"Copied: {len(report.copied)}")
    if report.overwritten:
        print(f"Overwritten: {len(report.overwritten)}")
    if report.skipped_existing:
        print(f"Skipped existing: {len(report.skipped_existing)}")
    if report.backups:
        print(f"Backups: {len(report.backups)}")
    if report.requirements_added:
        print(f"requirements.txt added lines: {len(report.requirements_added)}")
    if report.gitignore_added:
        print(f".gitignore added lines: {report.gitignore_added}")
    if report.warnings:
        print("Warnings:")
        for w in report.warnings:
            print(f"  - {w}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Invoker into one or more projects")
    parser.add_argument("dest", nargs="*", help="Destination project root(s)")
    parser.add_argument(
        "--pick-dest",
        action="store_true",
        help="Open a folder picker to select a single destination project root (GUI)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument(
        "--overwrite-framework",
        action="store_true",
        help="Overwrite existing framework files (agent/, agent_tools/, instructions/, .clinerules, agent_framework_config.yaml)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="When overwriting/migrating, store backups under <dest>/.invoker_backups/<timestamp>/",
    )
    parser.add_argument(
        "--migrate-legacy-instructions",
        action="store_true",
        help="Move legacy instruction files (old paths) to instructions/legacy/ before copying",
    )
    parser.add_argument("--skip-framework", action="store_true", help="Skip copying framework footprint")
    parser.add_argument("--skip-requirements", action="store_true", help="Skip requirements.txt merge/copy")
    parser.add_argument("--skip-gitignore", action="store_true", help="Skip .gitignore merge/copy")
    args = parser.parse_args()

    if args.pick_dest and args.dest:
        raise SystemExit("--pick-dest cannot be combined with positional destinations.")

    root = invoker_root()
    inv_reqs = root / "requirements.txt"
    inv_gitignore_host = root / "instructions" / "model_agnostic" / ".gitignore.host"

    if not args.skip_requirements and not inv_reqs.exists():
        raise SystemExit(f"Invoker requirements.txt not found: {inv_reqs}")
    if not args.skip_gitignore and not inv_gitignore_host.exists():
        raise SystemExit(f"Invoker gitignore.host not found: {inv_gitignore_host}")

    destinations = list(args.dest)
    if not destinations and not args.pick_dest:
        # UX default: if user didn't pass any dest, guide them through picking or typing one.
        args.pick_dest = True

    if args.pick_dest:
        selected = ""
        picker_error: Optional[str] = None
        try:
            import tkinter as tk
            from tkinter import filedialog

            root_tk = tk.Tk()
            root_tk.withdraw()
            selected = filedialog.askdirectory(title="Select destination project root")
            root_tk.destroy()
        except Exception as exc:
            picker_error = str(exc)

        if not selected:
            if picker_error:
                print(f"Folder picker unavailable (tkinter): {picker_error}")
            print("Enter destination project root path (blank to cancel):")
            selected = strip_quotes(input("> ").strip())
            if not selected:
                raise SystemExit("No destination selected.")

        destinations = [selected]

    if not destinations:
        raise SystemExit("No destinations provided. Provide one or more <dest> or use --pick-dest.")

    for dest_str in destinations:
        dest_root = resolve_dest_root(dest_str)
        report = ChangeReport()

        detect_legacy(dest_root, report)
        backup_root = None
        if args.backup and (args.overwrite_framework or args.migrate_legacy_instructions):
            backup_root = dest_root / ".invoker_backups" / now_stamp()

        if args.migrate_legacy_instructions:
            migrate_legacy(dest_root, backup_root=backup_root, dry_run=args.dry_run, report=report)

        if not args.skip_framework:
            for item in framework_items():
                rel_name = item.name
                dest_item = dest_root / rel_name
                if item.is_dir():
                    copy_tree(
                        item,
                        dest_item,
                        dest_root,
                        overwrite=args.overwrite_framework,
                        backup_root=backup_root,
                        dry_run=args.dry_run,
                        report=report,
                    )
                else:
                    copy_file(
                        item,
                        dest_root,
                        dest_item,
                        overwrite=args.overwrite_framework,
                        backup_root=backup_root,
                        dry_run=args.dry_run,
                        report=report,
                    )

        if not args.skip_requirements:
            merge_requirements(inv_reqs, dest_root / "requirements.txt", dry_run=args.dry_run, report=report)

        if not args.skip_gitignore:
            merge_gitignore(inv_gitignore_host, dest_root / ".gitignore", dry_run=args.dry_run, report=report)

        print_report(dest_root, report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
