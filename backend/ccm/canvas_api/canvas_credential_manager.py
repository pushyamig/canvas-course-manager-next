import logging
from typing import List, Union
from django.conf import settings
from canvas_oauth.oauth import get_oauth_token
from rest_framework.request import Request
from canvas_oauth.exceptions import InvalidOAuthReturnError

from canvasapi import Canvas
from canvasapi.exceptions import (InvalidAccessToken, Unauthorized)
from .exceptions import CanvasAccessTokenException, CanvasHTTPError, HTTPAPIError, SerializerError 

logger = logging.getLogger(__name__)

class CanvasCredentialManager:

  def __init__(self):
    super().__init__()
    self.canvasURL = f"https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}"
  
  def get_canvasapi_instance(self, request: Request) -> Canvas:
    try:
      access_token = get_oauth_token(request)
    except InvalidOAuthReturnError as e:
      # This issue occurred during non-prod Canvas sync when the API key was deleted, but the token remained in CCM databases. Expired token will trigger the usecase.
      logger.error(f"InvalidOAuthReturnError for user: {request.user}. Remove invalid refresh_token and prompt for reauthentication.")
      raise CanvasAccessTokenException()
    return Canvas(self.canvasURL, access_token)
  
  def handle_serializer_errors(self, serializer_errors: dict, input: str) -> CanvasHTTPError:
      logger.error(f"Serializer error: {serializer_errors} occured during the API call.")
      # Create a SerializerError instance and pass it to CanvasHTTPError
      serializer_error_instance = SerializerError(failed_input=str(input), serializer_error=serializer_errors)
      err_response: CanvasHTTPError = CanvasHTTPError(serializer_error_instance)
      return err_response
  
  def handle_canvas_api_exceptions(self, exceptions: Union[HTTPAPIError, List[HTTPAPIError]]) -> CanvasHTTPError:
    logger.error(f"API error occurred: {exceptions}")
    exceptions = exceptions if isinstance(exceptions, list) else [exceptions]
    error_exceptions = [entry["error"] for entry in exceptions]
    
    if any(isinstance(exc, (InvalidAccessToken, Unauthorized)) for exc in error_exceptions):
      # Invalid access token occures when a user revokes Canvas Authorization from Canvas Profile settings.
      # Unauthorized happens when you add more API scopes but the User Authorization is still limited to eariler API scopes.
      raise CanvasAccessTokenException()
    
    return CanvasHTTPError(exceptions)
