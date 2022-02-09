import aiohttp

from settings import settings


async def if_http_request(url, method, data) -> dict:
    """Handles all http requests to the interface"""
    timeout = aiohttp.ClientTimeout(
        total=settings.CORE_REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # TODO (PHASE 2) add request encryption to interface
        if method == 'post':
            async with session.request(method, url, json=data) as response:
                return await response.json()
        else:
            async with session.request(method, url, params=data) as response:
                return await response.json()
