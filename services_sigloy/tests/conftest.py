import asyncio

import pytest

"""
This is configuration file for pytest to run async test in a new loop
"""


@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    """Without this we get runtime error (attached to different loop)"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


