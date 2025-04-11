from dataclasses import dataclass
from http import HTTPStatus
from typing import List, TypedDict, Union, Dict
from canvasapi.exceptions import (
    BadRequest, Conflict, Forbidden, InvalidAccessToken, RateLimitExceeded,
    ResourceDoesNotExist, Unauthorized, UnprocessableEntity
)
from canvas_oauth.exceptions import InvalidOAuthReturnError
from rest_framework.exceptions import APIException

@dataclass
class SerializerError():
    failed_input: str
    serializer_error: dict
    
class HTTPAPIError(Exception):
    """Custom exception to capture failed input along with the error details."""
    def __init__(self, failed_input: str, original_exception: Exception):
        self.failed_input = failed_input
        self.original_exception = original_exception

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the error."""
        return {"failed_input": self.failed_input, "error": self.original_exception}

class CanvasHTTPError():
    """
    Custom exception for HTTP errors originating from Canvas API interactions
    """

    canvas_error_prefix = 'An error occurred during Canvas API steps. '

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

    def __init__(self, error_data: Union[List[HTTPAPIError], SerializerError]) -> None:
        self.errors = []
        if isinstance(error_data, list) and all(isinstance(error, HTTPAPIError) for error in error_data):
            for error in error_data:
                self.errors.append({
                    "canvasStatusCode": self.EXCEPTION_STATUS_MAP.get(type(error.original_exception), HTTPStatus.INTERNAL_SERVER_ERROR.value),
                    "message": str(error.original_exception),
                    "failedInput": error.failed_input
                })
        elif isinstance(error_data, SerializerError):
            self.errors.append({
                "canvasStatusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
                "message": str(error_data.serializer_error),
                "failedInput": error_data.failed_input
            })
        else:
            self.errors.append({
                "canvasStatusCode": HTTPStatus.BAD_REQUEST.value,
                "message": error_data,
                "failedInput": None
            })

    def __str__(self) -> str:
        return f'Errors: {self.errors}'

    def to_dict(self) -> dict:
        return {
            "statusCode": (sc.pop() if len(sc := {e["canvasStatusCode"] for e in self.errors}) == 1 else HTTPStatus.INTERNAL_SERVER_ERROR.value),
            "errors": self.errors
        }
    
class CanvasAccessTokenException(APIException):
    """
    Custom exception for Canvas token-related errors.
    """
    status_code = 401
    default_detail = 'Unauthorized'
    default_code = 'unauthorized'

    def __init__(self, detail=None, code=None):
        self.redirect = True
        super().__init__(detail or self.default_detail, code)

    def to_dict(self) -> dict:
        return {
            "message": self.detail,
            "statusCode": self.status_code,
            "redirect": self.redirect
        }