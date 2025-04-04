# https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
from rest_framework.views import exception_handler
from rest_framework.response import Response
from http import HTTPStatus

from .exceptions import CanvasAccessTokenException

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, CanvasAccessTokenException):
        data = exc.to_dict()
        return Response(data, status=data.get("statusCode", HTTPStatus.UNAUTHORIZED.value))

    return response