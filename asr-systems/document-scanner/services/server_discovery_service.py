"""
Server Discovery Service
Automatically discover ASR Production Servers on local network and cloud
"""

import asyncio
import logging
import socket
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass
import aiohttp

# Import shared components
from shared.core.exceptions import NetworkError

# Import scanner config
from ..config.scanner_settings import scanner_settings

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredServer:
    """Discovered production server information"""
    url: str
    name: str
    version: str
    capabilities: List[str]
    health_status: str
    discovered_at: datetime
    response_time_ms: float
    location: str  # "local" or "cloud"


class ServerDiscoveryService:
    """
    Service for discovering ASR Production Servers

    Features:
    - Local network discovery via broadcast
    - Manual server configuration
    - Health checking and response time monitoring
    - Automatic failover between servers
    - Cloud server discovery
    """

    def __init__(self):
        self.discovered_servers: Dict[str, DiscoveredServer] = {}
        self.manual_servers: Set[str] = set()
        self.last_discovery: Optional[datetime] = None
        self.discovery_interval = 300  # 5 minutes
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize server discovery service"""
        try:
            logger.info("🚀 Initializing Server Discovery Service...")

            # Load manual server configurations
            await self._load_manual_servers()

            # Initial discovery
            if scanner_settings.server_discovery_enabled:
                await self._perform_discovery()

            self.initialized = True
            logger.info(f"✅ Server Discovery Service initialized:")
            logger.info(f"   • {len(self.discovered_servers)} servers discovered")
            logger.info(f"   • Discovery enabled: {scanner_settings.server_discovery_enabled}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Server Discovery Service: {e}")
            raise NetworkError(f"Server discovery initialization failed: {e}")

    async def _load_manual_servers(self) -> None:
        """Load manually configured servers"""
        try:
            # Default server configurations
            default_servers = [
                "http://localhost:8000",  # Local development
                "https://api.asr-records.com",  # Production cloud
            ]

            # Add servers from environment or config
            env_servers = scanner_settings.dict().get('manual_servers', [])
            all_servers = default_servers + env_servers

            for server_url in all_servers:
                self.manual_servers.add(server_url)
                logger.info(f"📝 Added manual server: {server_url}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load manual servers: {e}")

    async def discover_servers(self) -> List[DiscoveredServer]:
        """Discover available production servers"""
        try:
            if not self.initialized:
                raise NetworkError("Server discovery service not initialized")

            # Check if we need to perform discovery
            now = datetime.now()
            if (self.last_discovery is None or
                now - self.last_discovery > timedelta(seconds=self.discovery_interval)):
                await self._perform_discovery()

            # Return discovered servers sorted by response time
            servers = list(self.discovered_servers.values())
            servers.sort(key=lambda s: s.response_time_ms)

            logger.info(f"🔍 Discovered {len(servers)} available servers")
            return servers

        except Exception as e:
            logger.error(f"❌ Server discovery failed: {e}")
            return []

    async def _perform_discovery(self) -> None:
        """Perform actual server discovery"""
        try:
            logger.info("🔍 Starting server discovery...")

            # Clear previous results
            self.discovered_servers.clear()

            # Discover local network servers
            if scanner_settings.server_discovery_enabled:
                await self._discover_local_servers()

            # Check manual servers
            await self._check_manual_servers()

            # Check cloud servers
            await self._discover_cloud_servers()

            self.last_discovery = datetime.now()

            logger.info(f"✅ Discovery complete: {len(self.discovered_servers)} servers found")

        except Exception as e:
            logger.error(f"❌ Discovery process failed: {e}")

    async def _discover_local_servers(self) -> None:
        """Discover servers on local network via broadcast"""
        try:
            logger.info("🔍 Scanning local network for ASR servers...")

            # Get local network ranges to scan
            local_ranges = await self._get_local_network_ranges()

            # Scan common ports for ASR servers
            common_ports = [8000, 8080, 80, 443]

            tasks = []
            for network_range in local_ranges:
                for port in common_ports:
                    task = self._check_server_at_address(network_range, port)
                    tasks.append(task)

            # Execute discovery tasks with timeout
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=scanner_settings.server_discovery_timeout
            )

        except asyncio.TimeoutError:
            logger.warning("⚠️ Local network discovery timed out")
        except Exception as e:
            logger.warning(f"⚠️ Local network discovery failed: {e}")

    async def _get_local_network_ranges(self) -> List[str]:
        """Get local network IP ranges to scan"""
        try:
            # Get local IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            # Extract network base (assuming /24 subnet)
            ip_parts = local_ip.split('.')
            network_base = '.'.join(ip_parts[:3])

            # Generate range of IPs to check (limited scan)
            ranges = []
            for i in [1, 100, 101, 102, 200, 201, 250]:  # Common server IPs
                ranges.append(f"{network_base}.{i}")

            return ranges

        except Exception as e:
            logger.warning(f"⚠️ Failed to get local network ranges: {e}")
            return []

    async def _check_server_at_address(self, ip_address: str, port: int) -> None:
        """Check if ASR server is running at specific address"""
        try:
            server_url = f"http://{ip_address}:{port}"

            # Quick health check
            server_info = await self._check_server_health(server_url)
            if server_info:
                self.discovered_servers[server_url] = server_info

        except Exception:
            # Silently ignore connection failures during scanning
            pass

    async def _check_manual_servers(self) -> None:
        """Check manually configured servers"""
        try:
            logger.info("📝 Checking manual servers...")

            tasks = [
                self._check_server_health(server_url)
                for server_url in self.manual_servers
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for server_url, result in zip(self.manual_servers, results):
                if isinstance(result, DiscoveredServer):
                    self.discovered_servers[server_url] = result
                    logger.info(f"✅ Manual server available: {server_url}")
                else:
                    logger.warning(f"⚠️ Manual server unavailable: {server_url}")

        except Exception as e:
            logger.warning(f"⚠️ Manual server check failed: {e}")

    async def _discover_cloud_servers(self) -> None:
        """Discover cloud-based ASR servers"""
        try:
            logger.info("☁️ Checking cloud servers...")

            # Known cloud endpoints
            cloud_servers = [
                "https://api.asr-records.com",
                "https://production.asr-records.com",
                "https://asr-records-alb-757932068.us-west-2.elb.amazonaws.com",
            ]

            tasks = [
                self._check_server_health(server_url)
                for server_url in cloud_servers
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for server_url, result in zip(cloud_servers, results):
                if isinstance(result, DiscoveredServer):
                    result.location = "cloud"  # Mark as cloud server
                    self.discovered_servers[server_url] = result
                    logger.info(f"☁️ Cloud server available: {server_url}")

        except Exception as e:
            logger.warning(f"⚠️ Cloud server discovery failed: {e}")

    async def _check_server_health(self, server_url: str) -> Optional[DiscoveredServer]:
        """Check health of specific server"""
        try:
            start_time = datetime.now()

            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Try to get server health endpoint
                async with session.get(f"{server_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()

                        # Get server info endpoint
                        async with session.get(f"{server_url}/api/info") as info_response:
                            if info_response.status == 200:
                                server_info = await info_response.json()
                            else:
                                server_info = {}

                        # Calculate response time
                        response_time = (datetime.now() - start_time).total_seconds() * 1000

                        return DiscoveredServer(
                            url=server_url,
                            name=server_info.get("name", "ASR Production Server"),
                            version=server_info.get("version", "unknown"),
                            capabilities=server_info.get("capabilities", ["document_processing"]),
                            health_status=health_data.get("status", "unknown"),
                            discovered_at=datetime.now(),
                            response_time_ms=response_time,
                            location="local" if "localhost" in server_url or server_url.startswith("http://192.168") else "remote"
                        )

        except Exception:
            # Server not available or not an ASR server
            pass

        return None

    async def get_best_server(self) -> Optional[DiscoveredServer]:
        """Get the best available server (lowest latency, healthy)"""
        try:
            servers = await self.discover_servers()

            if not servers:
                return None

            # Filter healthy servers
            healthy_servers = [s for s in servers if s.health_status == "healthy"]

            if not healthy_servers:
                # No healthy servers, return the best available
                return servers[0] if servers else None

            # Return server with lowest response time
            return healthy_servers[0]

        except Exception as e:
            logger.error(f"❌ Failed to get best server: {e}")
            return None

    async def add_manual_server(self, server_url: str) -> bool:
        """Add a manual server configuration"""
        try:
            # Validate server URL
            if not server_url.startswith(('http://', 'https://')):
                server_url = f"http://{server_url}"

            # Check if server is available
            server_info = await self._check_server_health(server_url)

            if server_info:
                self.manual_servers.add(server_url)
                self.discovered_servers[server_url] = server_info
                logger.info(f"✅ Added manual server: {server_url}")
                return True
            else:
                logger.warning(f"⚠️ Server not available: {server_url}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to add manual server: {e}")
            return False

    async def remove_manual_server(self, server_url: str) -> bool:
        """Remove a manual server configuration"""
        try:
            if server_url in self.manual_servers:
                self.manual_servers.remove(server_url)

            if server_url in self.discovered_servers:
                del self.discovered_servers[server_url]

            logger.info(f"🗑️ Removed manual server: {server_url}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to remove manual server: {e}")
            return False

    async def refresh_discovery(self) -> None:
        """Force refresh of server discovery"""
        try:
            logger.info("🔄 Forcing server discovery refresh...")
            self.last_discovery = None
            await self._perform_discovery()

        except Exception as e:
            logger.error(f"❌ Discovery refresh failed: {e}")

    async def get_server_list(self) -> List[Dict[str, Any]]:
        """Get list of all discovered servers with details"""
        try:
            servers = []

            for server in self.discovered_servers.values():
                servers.append({
                    "url": server.url,
                    "name": server.name,
                    "version": server.version,
                    "capabilities": server.capabilities,
                    "health_status": server.health_status,
                    "response_time_ms": server.response_time_ms,
                    "location": server.location,
                    "discovered_at": server.discovered_at.isoformat(),
                    "is_manual": server.url in self.manual_servers
                })

            return servers

        except Exception as e:
            logger.error(f"❌ Failed to get server list: {e}")
            return []

    async def get_health(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            if not self.initialized:
                return {"status": "not_initialized"}

            server_count = len(self.discovered_servers)
            healthy_servers = len([s for s in self.discovered_servers.values()
                                  if s.health_status == "healthy"])

            return {
                "status": "healthy",
                "servers_discovered": server_count,
                "healthy_servers": healthy_servers,
                "manual_servers": len(self.manual_servers),
                "last_discovery": self.last_discovery.isoformat() if self.last_discovery else None,
                "discovery_enabled": scanner_settings.server_discovery_enabled
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def cleanup(self) -> None:
        """Cleanup server discovery service"""
        logger.info("🧹 Cleaning up Server Discovery Service...")
        self.discovered_servers.clear()
        self.initialized = False