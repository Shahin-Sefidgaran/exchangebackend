import glob
import importlib

from db.pgsql.engine import engine, Base
from scripts.commands.seed import seed


def import_models():
    models = glob.glob('*/models.py')
    for m in models:
        m = m.replace('/', '.').replace('.py', '')
        importlib.import_module(m)


async def migrate(seed_db=False):
    import_models()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    if seed_db:
        await seed()
