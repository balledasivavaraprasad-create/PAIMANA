import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.errors import DomainError, ErrorCode


def error_body(code: str, message: str, request_id: str, details: dict | None = None) -> dict:
    payload = {"error": {"code": code, "message": message, "request_id": request_id}}
    if details:
        payload["error"]["details"] = details
    return payload


async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except DomainError as exc:
        return JSONResponse(
            status_code=exc.http_status,
            content=error_body(exc.code.value, exc.message, request_id, exc.details),
        )
    response.headers["X-Request-ID"] = request_id
    return response


def install_exception_handlers(app):
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=exc.http_status,
            content=error_body(exc.code.value, exc.message, request_id, exc.details),
        )
