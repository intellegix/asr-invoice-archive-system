"""
Unit Tests for Scanner Manager Service
Tests registration, heartbeat, timeout, client listing.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "production-server"))

from production_server.services.scanner_manager_service import (
    ScannerManagerService,
    ScannerUploadRequest,
)


@pytest.fixture
async def scanner_service():
    svc = ScannerManagerService(max_clients=5)
    # Bypass actual background tasks in tests
    with patch.object(svc, "_monitor_heartbeats", new_callable=AsyncMock):
        with patch.object(svc, "_cleanup_stale_sessions", new_callable=AsyncMock):
            svc.initialized = True
    return svc


async def _register_scanner(svc, scanner_id="scanner-001", name="Test Scanner"):
    return await svc.register_scanner(
        scanner_id=scanner_id,
        name=name,
        version="1.0.0",
        capabilities=["scan", "ocr"],
        ip_address="192.168.1.100",
        tenant_id="test-tenant",
    )


class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_scanner(self, scanner_service):
        result = await _register_scanner(scanner_service)

        assert result["status"] == "registered"
        assert result["scanner_id"] == "scanner-001"
        assert "upload_endpoints" in result

    @pytest.mark.asyncio
    async def test_max_clients_enforced(self, scanner_service):
        for i in range(5):
            await _register_scanner(scanner_service, scanner_id=f"scanner-{i}")

        with pytest.raises(Exception, match="Maximum scanner clients exceeded"):
            await _register_scanner(scanner_service, scanner_id="scanner-overflow")

    @pytest.mark.asyncio
    async def test_connected_scanners_list(self, scanner_service):
        await _register_scanner(scanner_service, scanner_id="s1", name="Scanner A")
        await _register_scanner(scanner_service, scanner_id="s2", name="Scanner B")

        scanners = await scanner_service.get_connected_scanners()
        assert len(scanners) == 2
        names = {s["name"] for s in scanners}
        assert names == {"Scanner A", "Scanner B"}


class TestHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_updates_timestamp(self, scanner_service):
        await _register_scanner(scanner_service)

        before = scanner_service.connected_scanners["scanner-001"].last_heartbeat
        result = await scanner_service.update_heartbeat("scanner-001")

        assert result is True
        after = scanner_service.connected_scanners["scanner-001"].last_heartbeat
        assert after >= before

    @pytest.mark.asyncio
    async def test_heartbeat_unknown_scanner(self, scanner_service):
        result = await scanner_service.update_heartbeat("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_heartbeat_updates_status(self, scanner_service):
        await _register_scanner(scanner_service)

        await scanner_service.update_heartbeat(
            "scanner-001", status_data={"status": "busy", "upload_count": 5}
        )

        scanner = scanner_service.connected_scanners["scanner-001"]
        assert scanner.status == "busy"
        assert scanner.upload_count == 5


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_scanner(self, scanner_service):
        await _register_scanner(scanner_service)
        assert len(scanner_service.connected_scanners) == 1

        result = scanner_service.disconnect_scanner("scanner-001")
        assert result is True
        assert len(scanner_service.connected_scanners) == 0

    @pytest.mark.asyncio
    async def test_disconnect_unknown_scanner(self, scanner_service):
        result = scanner_service.disconnect_scanner("nonexistent")
        assert result is False


class TestContentType:
    def test_pdf_detection(self, scanner_service):
        assert scanner_service._detect_content_type("doc.pdf") == "application/pdf"

    def test_jpeg_detection(self, scanner_service):
        assert scanner_service._detect_content_type("photo.jpg") == "image/jpeg"

    def test_png_detection(self, scanner_service):
        assert scanner_service._detect_content_type("scan.png") == "image/png"

    def test_unknown_extension(self, scanner_service):
        assert (
            scanner_service._detect_content_type("file.xyz")
            == "application/octet-stream"
        )


class TestHealth:
    @pytest.mark.asyncio
    async def test_healthy(self, scanner_service):
        health = await scanner_service.get_health()
        assert health["status"] == "healthy"
        assert health["max_clients"] == 5

    @pytest.mark.asyncio
    async def test_not_initialized(self):
        svc = ScannerManagerService()
        health = await svc.get_health()
        assert health["status"] == "not_initialized"


class TestCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_disconnects_all(self, scanner_service):
        await _register_scanner(scanner_service, scanner_id="s1")
        await _register_scanner(scanner_service, scanner_id="s2")

        await scanner_service.cleanup()

        assert len(scanner_service.connected_scanners) == 0
        assert scanner_service.initialized is False
