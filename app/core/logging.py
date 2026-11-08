import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:  # Чтобы не навесить обработчики повторно
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )

    logging.getLogger("app").setLevel(logging.INFO)


logger = logging.getLogger("app.middleware")


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    started_at = perf_counter()
    try:
        response: Response = await call_next(request)  # Работа самого эндпоинта
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "Request failed: %s %s completed_in=%.2fms",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "%s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
