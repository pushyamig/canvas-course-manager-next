from http import HTTPStatus
import json
from typing import Any, List, TypedDict
from canvasapi.exceptions import (
    BadRequest, Conflict, Forbidden, InvalidAccessToken, RateLimitExceeded,
    ResourceDoesNotExist, Unauthorized, UnprocessableEntity
)
from canvas_oauth.exceptions import InvalidOAuthReturnError


class ErrorData(TypedDict):
    failed_input: str
    exeption: Exception
    
class CanvasHTTPError(Exception):
    """
    Custom exception for HTTP errors originating from Canvas API interactions
    """

    canvas_error_prefix = 'An error occurred while communicating with Canvas. '

    message: str
    status_code: int
    errors: List[dict]
    EXCEPTION_STATUS_MAP = {
        BadRequest: HTTPStatus.BAD_REQUEST.value,
        InvalidAccessToken: HTTPStatus.UNAUTHORIZED.value,
        Unauthorized: HTTPStatus.UNAUTHORIZED.value,
        Forbidden: HTTPStatus.FORBIDDEN.value,
        RateLimitExceeded: HTTPStatus.FORBIDDEN.value,
        ResourceDoesNotExist: HTTPStatus.NOT_FOUND.value,
        UnprocessableEntity: HTTPStatus.UNPROCESSABLE_ENTITY.value,
        Conflict: HTTPStatus.CONFLICT.value,
        InvalidOAuthReturnError: HTTPStatus.FORBIDDEN.value
    }

    def __init__(self, error_data: List[ErrorData]) -> None:
        self.errors = []
        for error in error_data:
            self.errors.append({
                "canvasStatusCode": self.EXCEPTION_STATUS_MAP.get(type(error['error']), HTTPStatus.INTERNAL_SERVER_ERROR.value),
                "message": str(error['error']),
                "failedInput": error['failed_input']
            })

    def __str__(self) -> str:
        return f'Errors: {self.errors}'

    def to_dict(self) -> dict:
        return {
            "statusCode": (sc.pop() if len(sc := {e["canvasStatusCode"] for e in self.errors}) == 1 else HTTPStatus.INTERNAL_SERVER_ERROR.value),
            "errors": self.errors
        }
class HTTPAPIError(Exception):
    """Custom exception to capture failed input along with the error details."""
    def __init__(self, failed_input: str, original_exception: Exception):
        self.failed_input = failed_input
        self.original_exception = original_exception
        super().__init__(f"Exception due failed input '{failed_input}': {original_exception}")

    def to_dict(self):
        """Returns a dictionary representation of the error."""
        return {"failed_input": self.failed_input, "error": self.original_exception}