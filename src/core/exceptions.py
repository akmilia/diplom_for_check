from logging import getLogger

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.responses import ORJSONResponse
from fastapi.utils import is_body_allowed_for_status_code
from fastapi.websockets import WebSocket
from starlette.exceptions import HTTPException

logger = getLogger(__name__)


def register_exceptions(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):  # type: ignore
        headers = getattr(exc, 'headers', None)
        if not is_body_allowed_for_status_code(exc.status_code):
            return Response(status_code=exc.status_code, headers=headers)
        return ORJSONResponse(
            status_code=exc.status_code, content={'detail': exc.detail}, headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore
        logger.warning(
            f'Validation Error: {exc.body}',
        )
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({'detail': exc.errors()}),
        )

    @app.exception_handler(WebSocketRequestValidationError)
    async def websocket_validation_exception_handler(  # type: ignore
        websocket: WebSocket,
        exc: WebSocketRequestValidationError,
    ):
        logger.warning(f'WebSocket Validation Error: {exc.errors()}')
        return await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=jsonable_encoder(exc.errors()),
        )

    return app
