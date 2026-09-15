"""Shared test setup.

`app.main` runs `Base.metadata.create_all(bind=engine)` at import time, which
would otherwise require a live Postgres connection. These are unit tests with
fully mocked repositories/services, so we neutralize that call before anything
imports `app.main`.
"""

from sqlalchemy.schema import MetaData

MetaData.create_all = lambda self, *args, **kwargs: None
