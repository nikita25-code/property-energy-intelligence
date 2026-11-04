"""Deployment regression checks for Docker Desktop / Windows compatibility."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sqlite_uses_docker_managed_volume_not_windows_bind_mount():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "./data:/app/data" in compose, "CSV and reports should remain host-accessible"
    assert "property_energy_db:/app/state" in compose
    assert "property_energy_db:" in compose
    assert "DB_PATH=/app/state/property_energy.sqlite3" in dockerfile
    assert "DB_PATH=/app/data/property_energy.sqlite3" not in dockerfile
