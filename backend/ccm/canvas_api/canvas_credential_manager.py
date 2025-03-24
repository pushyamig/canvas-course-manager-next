import logging
from http import HTTPStatus
from django.conf import settings
from canvas_oauth.oauth import get_oauth_token
from rest_framework.request import Request
from canvas_oauth.models import CanvasOAuth2Token
from canvas_oauth.exceptions import InvalidOAuthReturnError

from canvasapi import Canvas
from canvasapi.exceptions import (
    BadRequest, Conflict, Forbidden, InvalidAccessToken, RateLimitExceeded,
    ResourceDoesNotExist, Unauthorized, UnprocessableEntity
)
from .exceptions import CanvasHTTPError 

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
  
  def handle_canvas_api_exception(self, exception: Exception, request: Request, input: str = None) -> CanvasHTTPError:
    logger.error(f"API error occcured : {exception}")
    self.handle_revoked_token(exception, request)
    
    for class_key in self.EXCEPTION_STATUS_MAP:
        if isinstance(exception, class_key):
            return CanvasHTTPError(str(exception), self.EXCEPTION_STATUS_MAP[class_key], input)
    return CanvasHTTPError(str(exception), HTTPStatus.INTERNAL_SERVER_ERROR.value, input)

  def handle_revoked_token(self, exception, request):
      if isinstance(exception, (InvalidAccessToken, InvalidOAuthReturnError)):
          CanvasOAuth2Token.objects.filter(user=request.user).delete()
          logger.error(f"Deleted the Canvas OAuth2 token for user: {request.user} since they might have revoked access.")
  
  def handle_serializer_errors(self, serializer_errors: dict, input: str = None) -> CanvasHTTPError:
      logger.error(f"Serializer error: {serializer_errors} occured during the API call.")
      err_response: CanvasHTTPError = CanvasHTTPError(serializer_errors, HTTPStatus.INTERNAL_SERVER_ERROR.value, str(input))
      return err_response
