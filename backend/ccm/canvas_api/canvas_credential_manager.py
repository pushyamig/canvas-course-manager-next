import logging
from http import HTTPStatus
from django.conf import settings
from canvas_oauth.oauth import get_oauth_token
from rest_framework.request import Request
from canvas_oauth.models import CanvasOAuth2Token
from canvas_oauth.exceptions import InvalidOAuthReturnError
from typing import Union, List

from canvasapi import Canvas
from canvasapi.exceptions import (
    BadRequest, Conflict, Forbidden, InvalidAccessToken, RateLimitExceeded,
    ResourceDoesNotExist, Unauthorized, UnprocessableEntity
)
from .exceptions import CanvasHTTPError, HTTPAPIError

logger = logging.getLogger(__name__)

class CanvasCredentialManager:
  
  # Map of Canvas API exceptions to HTTP status codes
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

  def __init__(self):
    super().__init__()
    self.canvasURL = f"https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}"
  
  def get_canvasapi_instance(self, request: HTTPStatus) -> Canvas:
    try:
      access_token = get_oauth_token(request)
    except InvalidOAuthReturnError as e:
      # This issue occurred during non-prod Canvas sync when the API key was deleted, but the token remained in CCM databases. Expired token will trigger the usecase.
      logger.error(f"InvalidOAuthReturnError for user: {request.user}. Remove invalid refresh_token and prompt for reauthentication.")
      raise InvalidOAuthReturnError(str(e))
    return Canvas(self.canvasURL, access_token)
  
  def handle_canvas_api_exceptions(self, exceptions: Union[HTTPAPIError, List[HTTPAPIError]], request: Request) -> CanvasHTTPError:
    logger.error(f"API error occurred: {exceptions}")
    exceptions = exceptions if isinstance(exceptions, list) else [exceptions]
     # Extract error exceptions
    error_exceptions = [entry["error"] for entry in exceptions]
    
    self.handle_revoked_token_1(error_exceptions, request)
    # return self.handle_err_response_1(exceptions)
    return self.handle_err_response_2(exceptions)
    # err_response: CanvasHTTPError = CanvasHTTPError(
    #     str(exceptions),
    #     HTTPStatus.INTERNAL_SERVER_ERROR.value,
    #     str(exceptions)
    # )
    # return err_response
  
  def handle_revoked_token_1(self, exceptions: List[Exception], request: Request):
     if any(isinstance(exc, (InvalidAccessToken, InvalidOAuthReturnError, Unauthorized)) for exc in exceptions):
        CanvasOAuth2Token.objects.filter(user=request.user).delete()
        logger.error(f"Deleted the Canvas OAuth2 token for user: {request.user} since they might have revoked access.")
  
  def handle_err_response_2(self, exceptions: List[HTTPAPIError]) -> CanvasHTTPError:
     error_list = []
     ar = CanvasHTTPError(exceptions)
     return ar

  
  def handle_err_response_1(self, exceptions: List[HTTPAPIError]) -> CanvasHTTPError:
     error_list = []
     for exc in exceptions:
        error_message = str(exc['error'])  # Extract the error message
        failed_input = exc['failed_input']  # Extract the failed input (section_name)

        # Determine the appropriate HTTP status code based on the exception type
        status_code = self.EXCEPTION_STATUS_MAP.get(type(exc['error']), HTTPStatus.INTERNAL_SERVER_ERROR.value)

        # error_entry = {
        #     "canvasStatusCode": status_code,
        #     "message": error_message,
        #     "failedInput": failed_input
        # }
        # CanvasHTTPError(error_message, status_code, failed_input)
        temp = CanvasHTTPError(error_message, status_code, failed_input)
        error_list.append(temp)
      # If there are multiple status codes, return a general failure code (502 Bad Gateway)
     final_status_code = status_code if len({error["canvasStatusCode"] for error in error_list}) == 1 else HTTPStatus.BAD_GATEWAY.value
     logger.error(f"Final status code: {final_status_code} for errors: {error_list}")
     return CanvasHTTPError(error_list, final_status_code)

  
     
  def handle_canvas_api_exception(self, exception: Exception, request: Request, input: str = None) -> CanvasHTTPError:
    logger.error(f"API error occcured : {exception}")
    
    self.handle_revoked_token(exception, request)
    return self.handle_err_response(exception, input)

  def handle_err_response(self, exception, input):
      status_code = next((self.EXCEPTION_STATUS_MAP[exc] for exc in self.EXCEPTION_STATUS_MAP if isinstance(exception, exc)), HTTPStatus.INTERNAL_SERVER_ERROR.value)
      return CanvasHTTPError(str(exception), status_code, input)

  def handle_revoked_token(self, exceptions: Union[Exception, List[Exception]], request: Request):
      exceptions = exceptions if isinstance(exceptions, list) else [exceptions]

      if any(isinstance(exc, (InvalidAccessToken, InvalidOAuthReturnError, Unauthorized)) for exc in exceptions):
        CanvasOAuth2Token.objects.filter(user=request.user).delete()
        logger.error(f"Deleted the Canvas OAuth2 token for user: {request.user} since they might have revoked access.")
  
  def handle_serializer_errors(self, serializer_errors: dict, input: str = None) -> CanvasHTTPError:
      logger.error(f"Serializer error: {serializer_errors} occured during the API call.")
      err_response: CanvasHTTPError = CanvasHTTPError(serializer_errors, HTTPStatus.INTERNAL_SERVER_ERROR.value, str(input))
      return err_response
