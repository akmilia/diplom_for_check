from uvicorn import Config, Server
from core.config import settings
from core.log import config as log_config

def main():
    config = Config(
        app="core.main:app",
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