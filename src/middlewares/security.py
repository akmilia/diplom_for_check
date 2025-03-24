from logging import getLogger

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.logger = getLogger(__name__)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        async def send_wrapper(message: Message) -> None:
            if message['type'] == 'http.response.start':
                message['headers'] = message['headers'] + [
                    (b'Strict-Transport-Security', b'max-age=63072000; includeSubDomains'),
                    (b'X-Frame-Options', b'DENY'),
                    (b'X-Content-Type-Options', b'nosniff'),
                    (b'X-XSS-Protection', b'1; mode=block'),
                ]

            await send(message)

        return await self.app(scope, receive, send_wrapper)
