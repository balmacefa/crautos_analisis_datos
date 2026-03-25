"""
cli.py — Argparse CLI for db_tools import/export.

Usage
-----
  python -m db_tools export --format json   --db PATH --out PATH [--tables TABLE ...]
  python -m db_tools export --format csv    --db PATH --out PATH
  python -m db_tools export --format sqlite --db PATH --out PATH

  python -m db_tools import --format json   --db PATH --src PATH [--dry-run]
  python -m db_tools import --format csv    --db PATH --src PATH [--dry-run]
  python -m db_tools import --format sqlite --db PATH --src PATH [--dry-run]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from db_tools.exporter import export
from db_tools.importer import import_db


_DEFAULT_DB = os.environ.get("SCRAPER_DB_PATH", "./data/crautos.db")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="db_tools",
        description="CrAutos database import / export tooling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples
--------
  # Export everything to JSON
  python -m db_tools export --format json --db ./data/crautos.db --out backup.json

  # Export car_details to CSV
  python -m db_tools export --format csv --db ./data/crautos.db --out cars.csv

  # Create a binary SQLite backup
  python -m db_tools export --format sqlite --db ./data/crautos.db --out backup.db

  # Dry-run import to check what would happen
  python -m db_tools import --format json --db ./data/crautos.db --src backup.json --dry-run

  # Restore from JSON
  python -m db_tools import --format json --db ./data/crautos.db --src backup.json
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── export ──────────────────────────────────────────────────────────────
    exp = sub.add_parser("export", help="Export the database to a file.")
    exp.add_argument(
        "--format", "-f",
        required=True,
        choices=["json", "csv", "sqlite"],
        dest="fmt",
        help="Output format (json | csv | sqlite).",
    )
    exp.add_argument(
        "--db",
        default=_DEFAULT_DB,
        metavar="PATH",
        help=f"Path to the SQLite database (default: {_DEFAULT_DB}).",
    )
    exp.add_argument(
        "--out", "-o",
        required=False,
        default=None,
        metavar="PATH",
        help="Output file path. Defaults to migration_data/backup_<timestamp>.<ext>.",
    )
    exp.add_argument(
        "--tables",
        nargs="+",
        default=None,
        metavar="TABLE",
        help=(
            "(JSON only) Tables to include. "
            "Default: scrape_runs car_urls car_details pagination_progress."
        ),
    )
    exp.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")

    # ── import ──────────────────────────────────────────────────────────────
    imp = sub.add_parser("import", help="Import data from a previously exported file.")
    imp.add_argument(
        "--format", "-f",
        required=True,
        choices=["json", "csv", "sqlite"],
        dest="fmt",
        help="Source format (json | csv | sqlite).",
    )
    imp.add_argument(
        "--db",
        default=_DEFAULT_DB,
        metavar="PATH",
        help=f"Path to the SQLite database (default: {_DEFAULT_DB}).",
    )
    imp.add_argument(
        "--src", "-s",
        required=True,
        metavar="PATH",
        help="Source file to import from.",
    )
    imp.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and parse without writing any changes to the database.",
    )
    imp.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        if args.command == "export":
            _run_export(args)
        elif args.command == "import":
            _run_import(args)
        else:
            parser.print_help()
            sys.exit(1)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("%s", exc)
        sys.exit(1)


def _run_export(args: argparse.Namespace) -> None:
    db  = Path(args.db)
    out = Path(args.out) if args.out else None

    if not out:
        from db_tools.exporter import get_default_export_path
        out = get_default_export_path(fmt=args.fmt)

    print(f"[db_tools] EXPORT  format={args.fmt}  db={db}  out={out}")

    if not db.exists():
        raise FileNotFoundError(f"Database not found: {db}")

    export(fmt=args.fmt, db_path=db, out_path=out, tables=getattr(args, "tables", None))

    size_kb = out.stat().st_size / 1024
    print(f"[db_tools] ✓ Export complete → {out}  ({size_kb:.1f} KB)")


def _run_import(args: argparse.Namespace) -> None:
    db  = Path(args.db)
    src = Path(args.src)

    print(f"[db_tools] IMPORT  format={args.fmt}  db={db}  src={src}  dry_run={args.dry_run}")

    summary = import_db(fmt=args.fmt, db_path=db, src_path=src, dry_run=args.dry_run)

    tag = "[dry-run]" if args.dry_run else "✓"
    print(f"[db_tools] {tag} Import complete. Summary: {summary}")
