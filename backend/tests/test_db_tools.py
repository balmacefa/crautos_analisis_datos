"""
test_db_tools.py — Unit tests for backend/db_tools (exporter + importer + CLI).

Run:
    cd c:/Users/fabia/OneDrive/Escritorio/repos/crautos_analisis_datos/backend
    python -m pytest tests/test_db_tools.py -v
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path

import pytest

# Ensure backend/ is on the path when running from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_tools.exporter import export_csv, export_json, export_sqlite
from db_tools.importer import import_csv, import_json, import_sqlite


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    """Create a minimal CrAutos SQLite DB with one car."""
    db = tmp_path / "test_crautos.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS scrape_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL DEFAULT 'running',
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS car_urls (
            url TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            scraped_at TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            last_seen_at TEXT
        );
        CREATE TABLE IF NOT EXISTS car_details (
            car_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            raw_json TEXT NOT NULL,
            scraped_at TEXT NOT NULL,
            FOREIGN KEY (url) REFERENCES car_urls(url)
        );
        CREATE TABLE IF NOT EXISTS pagination_progress (
            run_id INTEGER PRIMARY KEY,
            last_page INTEGER NOT NULL DEFAULT 0,
            total_pages INTEGER NOT NULL DEFAULT 0,
            urls_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL
        );

        INSERT INTO car_urls VALUES ('https://example.com/car/1', 'done', 0, '2024-01-01T00:00:00+00:00', '2024-01-02T00:00:00+00:00', 1, '2024-01-02T00:00:00+00:00');
        INSERT INTO car_urls VALUES ('https://example.com/car/2', 'done', 0, '2024-01-01T00:00:00+00:00', '2024-01-02T00:00:00+00:00', 1, '2024-01-02T00:00:00+00:00');
        INSERT INTO car_details VALUES ('car-001', 'https://example.com/car/1', '{"marca":"Toyota","modelo":"Corolla","año":2020,"precio":15000}', '2024-01-02T00:00:00+00:00');
        INSERT INTO car_details VALUES ('car-002', 'https://example.com/car/2', '{"marca":"Honda","modelo":"Civic","año":2019,"precio":13000}', '2024-01-02T00:00:00+00:00');
        """
    )
    conn.commit()
    conn.close()
    return db


# ---------------------------------------------------------------------------
# Exporter tests
# ---------------------------------------------------------------------------

class TestExportJson:
    def test_creates_file(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        export_json(tmp_db, out)
        assert out.exists()

    def test_valid_json(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        export_json(tmp_db, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_contains_car_details(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        export_json(tmp_db, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "car_details" in data
        assert len(data["car_details"]) == 2

    def test_car_details_flattened(self, tmp_db: Path, tmp_path: Path) -> None:
        """raw_json should be expanded into top-level keys."""
        out = tmp_path / "export.json"
        export_json(tmp_db, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        first = data["car_details"][0]
        assert "raw_json" not in first
        assert "marca" in first

    def test_contains_meta(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        export_json(tmp_db, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "_meta" in data

    def test_custom_tables(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        export_json(tmp_db, out, tables=["car_urls"])
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "car_urls" in data
        assert "car_details" not in data

    def test_returns_row_count(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.json"
        total = export_json(tmp_db, out)
        assert total > 0


class TestExportCsv:
    def test_creates_file(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.csv"
        export_csv(tmp_db, out)
        assert out.exists()

    def test_has_header_row(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.csv"
        export_csv(tmp_db, out)
        with out.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames
        assert headers is not None
        assert "car_id" in headers
        assert "url" in headers

    def test_flattened_fields(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.csv"
        export_csv(tmp_db, out)
        with out.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 2
        assert "raw_json" not in rows[0]
        assert "marca" in rows[0]

    def test_returns_row_count(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "export.csv"
        count = export_csv(tmp_db, out)
        assert count == 2


class TestExportSqlite:
    def test_creates_file(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "backup.db"
        export_sqlite(tmp_db, out)
        assert out.exists()

    def test_backup_is_valid_sqlite(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "backup.db"
        export_sqlite(tmp_db, out)
        conn = sqlite3.connect(out)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        conn.close()
        assert result[0] == "ok"

    def test_backup_has_same_rows(self, tmp_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "backup.db"
        export_sqlite(tmp_db, out)
        conn = sqlite3.connect(out)
        count = conn.execute("SELECT COUNT(*) FROM car_details").fetchone()[0]
        conn.close()
        assert count == 2


# ---------------------------------------------------------------------------
# Importer tests
# ---------------------------------------------------------------------------

class TestImportJson:
    def test_round_trip(self, tmp_db: Path, tmp_path: Path) -> None:
        """export → wipe car_details → import → same row count."""
        exported = tmp_path / "export.json"
        export_json(tmp_db, exported)

        # Wipe
        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM car_details")
        conn.commit()
        count_before = conn.execute("SELECT COUNT(*) FROM car_details").fetchone()[0]
        conn.close()
        assert count_before == 0

        # Import
        summary = import_json(tmp_db, exported)
        assert summary["car_details"] == 2

    def test_dry_run_no_write(self, tmp_db: Path, tmp_path: Path) -> None:
        exported = tmp_path / "export.json"
        export_json(tmp_db, exported)

        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM car_details")
        conn.commit()
        conn.close()

        import_json(tmp_db, exported, dry_run=True)

        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM car_details").fetchone()[0]
        conn.close()
        assert count == 0  # dry_run → no rows should have been written

    def test_missing_src_raises(self, tmp_db: Path, tmp_path: Path) -> None:
        from db_tools.importer import import_db
        with pytest.raises(FileNotFoundError):
            import_db("json", tmp_db, tmp_path / "nonexistent.json")


class TestImportCsv:
    def test_round_trip(self, tmp_db: Path, tmp_path: Path) -> None:
        exported = tmp_path / "export.csv"
        export_csv(tmp_db, exported)

        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM car_details")
        conn.commit()
        conn.close()

        summary = import_csv(tmp_db, exported)
        assert summary["car_details"] == 2

    def test_dry_run_no_write(self, tmp_db: Path, tmp_path: Path) -> None:
        exported = tmp_path / "export.csv"
        export_csv(tmp_db, exported)

        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM car_details")
        conn.commit()
        conn.close()

        import_csv(tmp_db, exported, dry_run=True)

        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM car_details").fetchone()[0]
        conn.close()
        assert count == 0


class TestImportSqlite:
    def test_restore(self, tmp_db: Path, tmp_path: Path) -> None:
        backup = tmp_path / "backup.db"
        export_sqlite(tmp_db, backup)

        # Wipe live db then restore
        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM car_details")
        conn.commit()
        conn.close()

        summary = import_sqlite(tmp_db, backup)
        assert "tables" in summary

        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM car_details").fetchone()[0]
        conn.close()
        assert count == 2

    def test_dry_run_no_write(self, tmp_db: Path, tmp_path: Path) -> None:
        backup = tmp_path / "backup.db"
        export_sqlite(tmp_db, backup)

        conn = sqlite3.connect(tmp_db)
        conn.execute("DELETE FROM car_details")
        conn.commit()
        conn.close()

        import_sqlite(tmp_db, backup, dry_run=True)

        conn = sqlite3.connect(tmp_db)
        count = conn.execute("SELECT COUNT(*) FROM car_details").fetchone()[0]
        conn.close()
        assert count == 0  # dry_run → untouched


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------

class TestCli:
    def test_help_exits_zero(self) -> None:
        from db_tools.cli import _build_parser
        parser = _build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0

    def test_export_json_via_cli(self, tmp_db: Path, tmp_path: Path) -> None:
        from db_tools.cli import main
        out = tmp_path / "cli_export.json"
        main(["export", "--format", "json", "--db", str(tmp_db), "--out", str(out)])
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "car_details" in data

    def test_import_json_dry_run_via_cli(self, tmp_db: Path, tmp_path: Path) -> None:
        from db_tools.cli import main
        exported = tmp_path / "export.json"
        main(["export", "--format", "json", "--db", str(tmp_db), "--out", str(exported)])
        # dry-run should not raise
        main(["import", "--format", "json", "--db", str(tmp_db), "--src", str(exported), "--dry-run"])

    def test_unknown_format_raises(self, tmp_db: Path, tmp_path: Path) -> None:
        from db_tools.cli import _build_parser
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["export", "--format", "xlsx", "--db", str(tmp_db), "--out", "x.xlsx"])
