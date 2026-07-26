from fastapi import Request, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

class ApplicationException(Exception):
    def __init__(self, 
                 message: str, 
                 status_code: int = status.HTTP_400_BAD_REQUEST, 
                 name: str = "ApplicationError"):
        self.message = message
        self.status_code = status_code
        self.name = name

async def application_exception_handler(request: Request, exc: ApplicationException):
    logger.error(
        "Application exception caught",
        url=str(request.url),
        method=request.method,
        error_name=exc.name,
        error_message=exc.message
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.name, "message": exc.message}
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception caught",
        url=str(request.url),
        method=request.method,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "InternalServerError", "message": "An unexpected error occurred."}
    )
