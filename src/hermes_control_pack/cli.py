from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import os

from . import __version__
from .analyzer import mechanism_markdown, signal_markdown
from .compiler import build_pack
from .corpus import build_index, write_index
from .doctor import doctor
from .installer import install_pack
from .state import ProjectStateStore

SOUL_PROFILES = ("balanced", "coder", "autonomous", "research")


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "~/.hermes"))


def parser() -> ArgumentParser:
    p = ArgumentParser(prog="hcp", description="Hermes Control Pack compiler, runtime installer, and continuity tools")
    p.add_argument("--version", action="version", version=f"hcp {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan every file in a corpus ZIP or directory")
    scan.add_argument("source", type=Path)
    scan.add_argument("--out", type=Path, default=Path("corpus-index.json"))

    analyze = sub.add_parser("analyze", help="Write an aggregate cross-source research signal report")
    analyze.add_argument("source", type=Path)
    analyze.add_argument("--out", type=Path, default=Path("RESEARCH_SIGNALS.md"))

    mech = sub.add_parser("mechanisms", help="Compile the cross-agent mechanism matrix from a corpus")
    mech.add_argument("source", type=Path)
    mech.add_argument("--out", type=Path, default=Path("MECHANISM_MATRIX.md"))

    build = sub.add_parser("build", help="Compile a Hermes-native control pack from a corpus")
    build.add_argument("source", type=Path)
    build.add_argument("--out", type=Path, default=Path("build/hcp"))

    install = sub.add_parser("install", help="Install HCP runtime assets (optionally from a compiled corpus build)")
    install.add_argument("--build", dest="build_dir", type=Path, help="Optional compiled HCP build; packaged runtime assets are used when omitted")
    install.add_argument("--project", type=Path, default=Path.cwd())
    install.add_argument("--hermes-home", type=Path, default=_hermes_home())
    install.add_argument("--force", action="store_true", help="Back up and replace differing HCP-managed files")
    install.add_argument("--no-context", action="store_true", help="Do not install project .hermes.md")
    install.add_argument("--no-skills", action="store_true", help="Do not install HCP skills")
    install.add_argument("--no-bundles", action="store_true", help="Do not install HCP skill bundles")
    install.add_argument("--no-plugin", action="store_true", help="Do not install the HCP Hermes runtime plugin")
    install.add_argument("--enable-plugin", action="store_true", help="Run `hermes plugins enable hcp-runtime` after install")
    install.add_argument("--soul", choices=SOUL_PROFILES, help="Install an HCP SOUL.md profile (existing file is protected)")
    install.add_argument("--context-engine", action="store_true", help="Install the optional hcp-continuity context engine")
    install.add_argument("--select-context-engine", action="store_true", help="Select hcp-continuity in Hermes config (implies --context-engine)")
    install.add_argument("--no-state", action="store_true", help="Do not initialize project-local .hcp/state")

    setup = sub.add_parser("setup", help="Recommended one-command HCP runtime setup for an existing Hermes installation")
    setup.add_argument("--project", type=Path, default=Path.cwd())
    setup.add_argument("--hermes-home", type=Path, default=_hermes_home())
    setup.add_argument("--force", action="store_true", help="Back up and replace differing HCP-managed runtime assets")
    setup.add_argument("--soul", choices=SOUL_PROFILES, default="balanced", help="Managed HCP SOUL overlay (default: balanced)")
    setup.add_argument("--no-soul", action="store_true", help="Do not add the HCP SOUL overlay")
    setup.add_argument("--no-context-engine", action="store_true", help="Keep Hermes' current context engine instead of selecting hcp-continuity")
    setup.add_argument("--project-context", action="store_true", help="Also install generic HCP .hermes.md into this project")

    state = sub.add_parser("state", help="Read or update project-local HCP continuity state")
    state_sub = state.add_subparsers(dest="state_command", required=True)
    show = state_sub.add_parser("show", help="Show persistent state")
    show.add_argument("--project", type=Path, default=Path.cwd())
    show.add_argument("--scope", choices=("summary", "project", "task", "decisions", "evidence", "trace"), default="summary")
    show.add_argument("--limit", type=int, default=30)
    set_state = state_sub.add_parser("set", help="Deep-merge a JSON object into PROJECT_STATE or TASK_STATE")
    set_state.add_argument("--project", type=Path, default=Path.cwd())
    set_state.add_argument("--scope", choices=("project", "task"), required=True)
    set_state.add_argument("--json", dest="json_value", required=True, help="JSON object to merge")
    set_state.add_argument("--replace", action="store_true")

    trace = sub.add_parser("trace", help="Print observable HCP harness telemetry (not chain-of-thought)")
    trace.add_argument("--project", type=Path, default=Path.cwd())
    trace.add_argument("--limit", type=int, default=50)

    souls = sub.add_parser("souls", help="List HCP SOUL profiles")

    check = sub.add_parser("doctor", help="Validate Python, compiled pack, Hermes integration, and target paths")
    check.add_argument("--build", dest="build_dir", type=Path)
    check.add_argument("--project", type=Path)
    check.add_argument("--hermes-home", type=Path, default=_hermes_home())
    return p


def _state_value(store: ProjectStateStore, scope: str, limit: int):
    if scope == "summary":
        return store.summary(decisions=min(limit, 20), evidence=min(limit, 30))
    if scope == "project":
        return store.read_project()
    if scope == "task":
        return store.read_task()
    if scope == "decisions":
        return store.decisions(limit)
    if scope == "evidence":
        return store.evidence(limit)
    if scope == "trace":
        return store.trace_events(limit)
    raise ValueError(scope)


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
    if args.command == "mechanisms":
        idx = build_index(args.source)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(mechanism_markdown(idx), encoding="utf-8")
        print(f"Mechanism matrix: {args.out.resolve()}")
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
            install_plugin=not args.no_plugin,
            enable_plugin=args.enable_plugin,
            soul_profile=args.soul,
            install_context_engine=args.context_engine or args.select_context_engine,
            select_context_engine=args.select_context_engine,
            initialize_state=not args.no_state,
        ):
            print(msg)
        return 0
    if args.command == "setup":
        for msg in install_pack(
            None,
            args.project,
            args.hermes_home,
            args.force,
            install_context=args.project_context,
            install_skills=True,
            install_bundles=True,
            install_plugin=True,
            enable_plugin=True,
            soul_profile=None if args.no_soul else args.soul,
            install_context_engine=not args.no_context_engine,
            select_context_engine=not args.no_context_engine,
            initialize_state=True,
        ):
            print(msg)
        print("Run `hcp doctor --project .` to verify the installed runtime.")
        return 0
    if args.command == "state":
        store = ProjectStateStore(args.project)
        if args.state_command == "show":
            print(json.dumps(_state_value(store, args.scope, args.limit), indent=2, ensure_ascii=False))
            return 0
        patch = json.loads(args.json_value)
        if not isinstance(patch, dict):
            raise SystemExit("--json must decode to an object")
        print(json.dumps(store.update(args.scope, patch, replace=args.replace), indent=2, ensure_ascii=False))
        return 0
    if args.command == "trace":
        store = ProjectStateStore(args.project)
        print(json.dumps(store.trace_events(args.limit), indent=2, ensure_ascii=False))
        return 0
    if args.command == "souls":
        print("\n".join(SOUL_PROFILES))
        return 0
    if args.command == "doctor":
        ok, lines = doctor(args.build_dir, args.project, args.hermes_home)
        print("\n".join(lines))
        return 0 if ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
