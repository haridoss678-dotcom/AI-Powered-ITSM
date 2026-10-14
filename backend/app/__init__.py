"""
Sorim.AI — Backend Application Package
"""

from __future__ import annotations

import anyio
import httpx


# httpx 0.28 removed the ASGITransport sync interface used by the older tests.
# Provide a small compatibility shim so `with Client(transport=ASGITransport(...))`
# continues to work while keeping the async implementation intact.
if not hasattr(httpx.ASGITransport, "__enter__"):
    def _asgi_transport_enter(self):
        return self

    def _asgi_transport_exit(self, exc_type, exc_value, traceback):
        return False

    def _asgi_transport_handle_request(self, request):
        async def _run():
            response = await self.handle_async_request(request)
            await response.aread()
            return httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=response.content,
                request=request,
                extensions=response.extensions,
                history=response.history,
                stream=httpx.ByteStream(response.content),
            )

        return anyio.run(_run)

    httpx.ASGITransport.__enter__ = _asgi_transport_enter
    httpx.ASGITransport.__exit__ = _asgi_transport_exit
    httpx.ASGITransport.handle_request = _asgi_transport_handle_request
