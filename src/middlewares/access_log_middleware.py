from logging import getLogger
from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class AccessLogMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.logger = getLogger(__name__)

    def get_client_ip(
        self, headers: list[tuple[bytes, bytes]], default_ip: str = '127.0.0.1'
    ) -> str:
        for h, v in headers:
            if h == b'x-forwarded-for':
                ips = v.decode().split(',')

                if len(ips) > 1:
                    return ips[-1].strip()

                return ips[0]

        return default_ip

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        start_time = perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message['type'] == 'http.response.start':
                headers = scope.get('headers', [])
                client_ip = self.get_client_ip(headers, scope['client'][0])

                response_time = (perf_counter() - start_time) * 1000

                message['headers'] = message['headers'] + [
                    (
                        b'Server-Timing',
                        f'resp;dur={response_time:.2f};desc="Response Time"'.encode(),
                    ),
                ]

                self.logger.info(
                    '%s - %s %s %d [%0.2fms]',
                    client_ip,
                    scope['method'],
                    scope['path'],
                    message['status'],
                    response_time,
                    extra={
                        'tags': {
                            'method': scope['method'],
                            'path': scope['path'],
                            'status': message['status'],
                            'response_time': response_time,
                            'client_ip': client_ip,
                        }
                    },
                )

            await send(message)

        return await self.app(scope, receive, send_wrapper)
