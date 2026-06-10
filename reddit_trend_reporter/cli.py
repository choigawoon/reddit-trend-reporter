"""`reddit-report` command-line entry point.

Subcommands:
  collect    fetch listings via rdt-cli and write report JSON
  report     analyze the latest snapshot with Claude
  pipeline   collect -> report (-> optional static build)
  init       scaffold a config file in the current directory
"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__, collect as collect_mod, pipeline as pipeline_mod, report as report_mod
from .config import CONFIG_RELPATH, default_config_text, load_config, resolve_config_path


def _base_dir(args: argparse.Namespace) -> Path:
    return (args.base_dir or Path.cwd()).resolve()


def _load(args: argparse.Namespace) -> tuple[dict, Path]:
    base = _base_dir(args)
    config = load_config(resolve_config_path(args.config, base))
    return config, base


def cmd_collect(args: argparse.Namespace) -> int:
    config, base = _load(args)
    report = collect_mod.collect(config)
    collect_mod.write_outputs(report, config, base)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    config, base = _load(args)
    report_mod.run(
        config,
        base,
        model=args.model,
        allow_fallback=args.allow_fallback,
        input_path=args.input,
    )
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    config, base = _load(args)
    report = collect_mod.collect(config)
    collect_mod.write_outputs(report, config, base)
    if not args.skip_llm:
        report_mod.run(config, base, model=args.model, allow_fallback=args.allow_fallback)
    if args.build:
        pipeline_mod.run_build(base)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    base = _base_dir(args)
    target = base / CONFIG_RELPATH
    if target.exists() and not args.force:
        print(f"config already exists: {target} (use --force to overwrite)")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(default_config_text())
    print(f"wrote {target}")
    print("Edit it, then run `reddit-report pipeline`.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reddit-report", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", type=Path, default=None, help="path to config JSON")
        p.add_argument("--base-dir", type=Path, default=None, help="base dir for outputs (default: cwd)")

    p_collect = sub.add_parser("collect", help="fetch listings and write report JSON")
    add_common(p_collect)
    p_collect.set_defaults(func=cmd_collect)

    p_report = sub.add_parser("report", help="analyze latest snapshot with Claude")
    add_common(p_report)
    p_report.add_argument("--input", type=Path, default=None, help="snapshot JSON (default: config output)")
    p_report.add_argument("--model", default=None)
    p_report.add_argument("--allow-fallback", action="store_true")
    p_report.set_defaults(func=cmd_report)

    p_pipeline = sub.add_parser("pipeline", help="collect -> report (-> optional build)")
    add_common(p_pipeline)
    p_pipeline.add_argument("--skip-llm", action="store_true")
    p_pipeline.add_argument("--allow-fallback", action="store_true")
    p_pipeline.add_argument("--model", default=None)
    p_pipeline.add_argument("--build", action="store_true", help="also run `npm run build` (needs the frontend)")
    p_pipeline.set_defaults(func=cmd_pipeline)

    p_init = sub.add_parser("init", help="scaffold a config file in the current directory")
    p_init.add_argument("--base-dir", type=Path, default=None)
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


# Thin entry points used by the backward-compat scripts/ shims.
def run_collect(argv: list[str] | None = None) -> int:
    return main(["collect", *(argv or [])])


def run_report(argv: list[str] | None = None) -> int:
    return main(["report", *(argv or [])])


def run_pipeline(argv: list[str] | None = None) -> int:
    return main(["pipeline", "--build", *(argv or [])])
