from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from middlewares.security import SecurityMiddleware

from .access_log_middleware import AccessLogMiddleware

logger = getLogger(__name__)


def register_middlewares(app: FastAPI):
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(AccessLogMiddleware)

    return app
