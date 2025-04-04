from uvicorn import Config, Server

from core.config import settings
from core.log import config as log_config

from fastapi import FastAPI

from database import lifespan

app = FastAPI( 
    version="1.0.0",
    debug=settings.DEBUG,
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    openapi_url='/v1/openapi.json' if settings.DEBUG else None,
    docs_url='/v1/docs' if settings.DEBUG else None,
    redoc_url='/v1/redoc' if settings.DEBUG else None,
    lifespan=lifespan
)


def main():
    config = Config(
        'core.main:app',
        host='0.0.0.0',
        port=5555,
        log_config=log_config,
        log_level='info',
        reload=settings.DEBUG,
        access_log=False,
    )
    server = Server(config)
    server.run()


if __name__ == '__main__':
    main()
