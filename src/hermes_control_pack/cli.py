from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import os

from . import __version__
from .analyzer import signal_markdown
from .compiler import build_pack
from .corpus import build_index, write_index
from .doctor import doctor
from .installer import install_pack


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "~/.hermes"))


def parser() -> ArgumentParser:
    p = ArgumentParser(prog="hcp", description="Hermes Control Pack compiler and installer")
    p.add_argument("--version", action="version", version=f"hcp {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan every file in a corpus ZIP or directory")
    scan.add_argument("source", type=Path)
    scan.add_argument("--out", type=Path, default=Path("corpus-index.json"))

    analyze = sub.add_parser("analyze", help="Write an aggregate cross-source research signal report")
    analyze.add_argument("source", type=Path)
    analyze.add_argument("--out", type=Path, default=Path("RESEARCH_SIGNALS.md"))

    build = sub.add_parser("build", help="Compile a Hermes-native control pack from a corpus")
    build.add_argument("source", type=Path)
    build.add_argument("--out", type=Path, default=Path("build/hcp"))

    install = sub.add_parser("install", help="Install a compiled pack into a project and Hermes home")
    install.add_argument("--build", dest="build_dir", type=Path, default=Path("build/hcp"))
    install.add_argument("--project", type=Path, default=Path.cwd())
    install.add_argument("--hermes-home", type=Path, default=_hermes_home())
    install.add_argument("--force", action="store_true", help="Back up and replace differing HCP-managed files")
    install.add_argument("--no-context", action="store_true", help="Do not install project .hermes.md")
    install.add_argument("--no-skills", action="store_true", help="Do not install HCP skills")
    install.add_argument("--no-bundles", action="store_true", help="Do not install HCP skill bundles")

    check = sub.add_parser("doctor", help="Validate Python, a compiled pack, and target paths")
    check.add_argument("--build", dest="build_dir", type=Path)
    check.add_argument("--project", type=Path)
    check.add_argument("--hermes-home", type=Path, default=_hermes_home())
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if args.command == "scan":
        idx = write_index(args.source, args.out)
        print(f"Scanned {idx['entry_count']} entries ({idx['text_entry_count']} text).")
        print(f"Fingerprint: {idx['source_sha256']}")
        print(f"Index: {args.out.resolve()}")
        return 0
    if args.command == "analyze":
        idx = build_index(args.source)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(signal_markdown(idx), encoding="utf-8")
        print(f"Report: {args.out.resolve()}")
        return 0
    if args.command == "build":
        idx = build_pack(args.source, args.out, root)
        print(f"Compiled pack from {idx['entry_count']} corpus entries.")
        print(f"Fingerprint: {idx['source_sha256']}")
        print(f"Output: {args.out.resolve()}")
        return 0
    if args.command == "install":
        for msg in install_pack(
            args.build_dir,
            args.project,
            args.hermes_home,
            args.force,
            install_context=not args.no_context,
            install_skills=not args.no_skills,
            install_bundles=not args.no_bundles,
        ):
            print(msg)
        return 0
    if args.command == "doctor":
        ok, lines = doctor(args.build_dir, args.project, args.hermes_home)
        print("\n".join(lines))
        return 0 if ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
