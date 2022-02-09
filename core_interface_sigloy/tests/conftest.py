import asyncio

import pytest


@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    """Without this we get runtime error (attached to different loop)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
