from contextlib import asynccontextmanager, contextmanager
from inspect import iscoroutinefunction, isasyncgenfunction

from fastapi.concurrency import contextmanager_in_threadpool
from starlette.concurrency import run_in_threadpool


# helpers to call dependencies manually


@asynccontextmanager
async def call_dependency_async(dependency, *args, **kwargs):
    # check if the function is async or not to choose correct context
    if iscoroutinefunction(dependency) or isasyncgenfunction(dependency):
        async with asynccontextmanager(dependency)(*args, **kwargs) as result:
            yield result
    else:
        async with contextmanager_in_threadpool(contextmanager(dependency)(*args, **kwargs)) as result:
            yield result
    # then will run remaining codes after "yield" keyword in dependency


@contextmanager
def call_dependency_sync(dependency, *args, **kwargs):
    with contextmanager(dependency)(*args, **kwargs) as result:
        yield result


# =====================================================
# helpers to call synchronous functions

async def sync_to_async(func, *args, **kwargs):
    return await run_in_threadpool(func, *args, **kwargs)

# =====================================================
