"""
Tests unitarios para cliente RouterOS.
Usa mocks para no requerir router físico.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from routeros.client import RouterOSClient
from routeros.models import RouterIdentity, ARPEntry, DHCPLease, SimpleQueue
from routeros.exceptions import (
    RouterOSAuthError,
    RouterOSNotFoundError,
    RouterOSConnectionError,
    RouterOSTimeoutError,
)


@pytest.fixture
def router_client():
    """Fixture: cliente RouterOS."""
    return RouterOSClient(
        host="192.168.88.1",
        port=80,
        username="test-user",
        password="test-pass",
    )


@pytest.fixture
async def connected_client(router_client):
    """Fixture: cliente RouterOS conectado."""
    with patch.object(router_client, "_request", new_callable=AsyncMock):
        router_client.connected = True
        router_client.client = MagicMock()
        yield router_client
        await router_client.disconnect()


class TestRouterOSClientInit:
    """Tests de inicialización."""

    def test_init_default_values(self):
        """Verifica valores por defecto."""
        client = RouterOSClient()
        assert client.host == "192.168.88.1"
        assert client.port == 80
        assert client.username == "api-container"
        assert client.timeout == 10.0
        assert client.max_retries == 3

    def test_init_custom_values(self):
        """Verifica valores personalizados."""
        client = RouterOSClient(
            host="10.0.0.1",
            port=443,
            username="custom",
            password="custom-pass",
            timeout=20.0,
        )
        assert client.host == "10.0.0.1"
        assert client.port == 443
        assert client.username == "custom"
        assert client.timeout == 20.0

    def test_base_url_construction(self):
        """Verifica construcción de URL base."""
        client = RouterOSClient(host="192.168.88.1", port=80)
        assert client.base_url == "http://192.168.88.1:80/rest"


class TestRouterOSClientConnect:
    """Tests de conexión."""

    @pytest.mark.asyncio
    async def test_connect_success(self, router_client):
        """Verifica conexión exitosa."""
        with patch.object(router_client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"name": "MikroTik"}
            await router_client.connect()

            assert router_client.connected is True
            assert router_client.client is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, router_client):
        """Verifica manejo de fallo de conexión."""
        with patch("httpx.AsyncClient", side_effect=Exception("Connection failed")):
            with pytest.raises(RouterOSConnectionError):
                await router_client.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, router_client):
        """Verifica desconexión."""
        # Simular conexión exitosa
        router_client.client = AsyncMock()
        router_client.connected = True

        await router_client.disconnect()

        router_client.client.aclose.assert_called_once()
        assert router_client.connected is False


class TestRouterOSClientRequest:
    """Tests de requests HTTP."""

    @pytest.mark.asyncio
    async def test_get_request_success(self, router_client):
        """Verifica GET request exitoso."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "1", "name": "device"}
        mock_response.text = ""

        with patch.object(router_client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            router_client.client = MagicMock()
            router_client.client.get = mock_get

            result = await router_client._request("GET", "/ip/arp")

            assert result == {"id": "1", "name": "device"}
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_401_unauthorized(self, router_client):
        """Verifica manejo de error 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        router_client.client = MagicMock()
        router_client.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(RouterOSAuthError):
            await router_client._request("GET", "/ip/arp")

    @pytest.mark.asyncio
    async def test_request_404_not_found(self, router_client):
        """Verifica manejo de error 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        router_client.client = MagicMock()
        router_client.client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(RouterOSNotFoundError):
            await router_client._request("GET", "/invalid/endpoint")

    @pytest.mark.asyncio
    async def test_request_retry_on_connection_error(self, router_client):
        """Verifica retry automático."""
        mock_error = httpx.ConnectError("Connection failed")
        router_client.client = MagicMock()
        router_client.client.get = AsyncMock(side_effect=mock_error)

        with pytest.raises(RouterOSConnectionError):
            await router_client._request("GET", "/ip/arp")


class TestRouterOSClientMethods:
    """Tests de métodos principales."""

    @pytest.mark.asyncio
    async def test_get_router_identity(self, connected_client):
        """Verifica obtener identidad del router."""
        connected_client._request = AsyncMock(
            return_value={"name": "hAP ac3", "platform": "RouterOS"}
        )

        identity = await connected_client.get_router_identity()

        assert isinstance(identity, RouterIdentity)
        assert identity.name == "hAP ac3"
        assert identity.platform == "RouterOS"

    @pytest.mark.asyncio
    async def test_get_arp_table(self, connected_client):
        """Verifica lectura de tabla ARP."""
        connected_client._request = AsyncMock(
            return_value=[
                {
                    "mac-address": "AA:BB:CC:DD:EE:FF",
                    "address": "192.168.88.100",
                    "interface": "bridge-lan",
                },
                {
                    "mac-address": "11:22:33:44:55:66",
                    "address": "192.168.88.101",
                    "interface": "bridge-lan",
                },
            ]
        )

        arp_table = await connected_client.get_arp_table()

        assert len(arp_table) == 2
        assert all(isinstance(entry, ARPEntry) for entry in arp_table)
        assert arp_table[0].mac_address == "AA:BB:CC:DD:EE:FF"

    @pytest.mark.asyncio
    async def test_get_dhcp_leases(self, connected_client):
        """Verifica lectura de leases DHCP."""
        connected_client._request = AsyncMock(
            return_value=[
                {
                    "mac-address": "AA:BB:CC:DD:EE:FF",
                    "address": "192.168.88.100",
                    "server": "dhcp-server",
                }
            ]
        )

        leases = await connected_client.get_dhcp_leases()

        assert len(leases) == 1
        assert isinstance(leases[0], DHCPLease)
        assert leases[0].mac_address == "AA:BB:CC:DD:EE:FF"

    @pytest.mark.asyncio
    async def test_add_to_address_list(self, connected_client):
        """Verifica agregar MAC a whitelist."""
        connected_client._request = AsyncMock(return_value={".id": "*123"})

        entry_id = await connected_client.add_to_address_list(
            "mac-whitelist", "AA:BB:CC:DD:EE:FF", "Test device"
        )

        assert entry_id == "*123"
        connected_client._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_queue(self, connected_client):
        """Verifica crear simple queue."""
        connected_client._request = AsyncMock(return_value={".id": "*456"})

        queue_id = await connected_client.create_queue(
            name="User-Queue",
            target="192.168.88.100/32",
            max_limit="5M/2M",
            priority=3,
        )

        assert queue_id == "*456"
        connected_client._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_dns_entry(self, connected_client):
        """Verifica agregar entrada DNS."""
        connected_client._request = AsyncMock(return_value={".id": "*789"})

        entry_id = await connected_client.add_dns_entry("facebook.com", "0.0.0.0")

        assert entry_id == "*789"
        connected_client._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_from_address_list(self, connected_client):
        """Verifica remover MAC de whitelist."""
        connected_client._request = AsyncMock(return_value={})

        result = await connected_client.remove_from_address_list("*123")

        assert result is True
        connected_client._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_queue(self, connected_client):
        """Verifica eliminar queue."""
        connected_client._request = AsyncMock(return_value={})

        result = await connected_client.delete_queue("*456")

        assert result is True
        connected_client._request.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_dns_entry(self, connected_client):
        """Verifica eliminar entrada DNS."""
        connected_client._request = AsyncMock(return_value={})

        result = await connected_client.delete_dns_entry("*789")

        assert result is True
        connected_client._request.assert_called_once()


class TestRouterOSClientHealth:
    """Tests de health check."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, connected_client):
        """Verifica health check exitoso."""
        connected_client._request = AsyncMock(return_value={"name": "MikroTik"})

        result = await connected_client.health_check()

        assert result.status == "ok"
        assert result.latency_ms > 0
        assert "MikroTik" in result.message

    @pytest.mark.asyncio
    async def test_health_check_failure(self, connected_client):
        """Verifica health check con fallo."""
        connected_client._request = AsyncMock(side_effect=Exception("Connection failed"))

        result = await connected_client.health_check()

        assert result.status == "error"
        assert "Connection failed" in result.message

    @pytest.mark.asyncio
    async def test_test_connection(self, connected_client):
        """Verifica test de conectividad simple."""
        connected_client._request = AsyncMock(return_value={"name": "MikroTik"})

        result = await connected_client.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, connected_client):
        """Verifica test de conectividad con fallo."""
        connected_client._request = AsyncMock(side_effect=RouterOSAuthError("test"))

        result = await connected_client.test_connection()

        assert result is False


class TestRouterOSClientContextManager:
    """Tests de context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self, router_client):
        """Verifica uso como context manager."""
        with patch.object(router_client, "connect", new_callable=AsyncMock):
            with patch.object(router_client, "disconnect", new_callable=AsyncMock):
                async with router_client:
                    pass

                router_client.connect.assert_called_once()
                router_client.disconnect.assert_called_once()
