from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, log_requests

configure_logging()
settings = get_settings()
app = FastAPI()
app.state.request_count = 0
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    expose_headers=["X-Request-Number"],
)
app.middleware("http")(log_requests)
app.include_router(api_router)


@app.middleware("http")
async def count_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Assign the number before awaiting, so concurrent requests keep their own number.
    app.state.request_count += 1
    request_number = app.state.request_count
    request.state.request_number = request_number

    response = await call_next(request)
    response.headers["X-Request-Number"] = str(request_number)
    return response


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Unhandled errors produce responses outside the HTTP middleware.
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={"X-Request-Number": str(request.state.request_number)},
    )
