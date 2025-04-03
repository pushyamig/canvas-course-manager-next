# https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from http import HTTPStatus

from .exceptions import CanvasAccessTokenException

def custom_exception_handler(exc, context):
    print("CUSTOM EXCEPTION HANDLER")
    response = exception_handler(exc, context)
    # if hasattr(exc, 'to_dict') and callable(getattr(exc, 'to_dict')):
    #     return Response(
    #         exc.to_dict(),
    #         status=exc.status_code if hasattr(exc, 'status_code') else HTTPStatus.INTERNAL_SERVER_ERROR
    #     )
    if isinstance(exc, CanvasAccessTokenException):
        return Response(
            {
                "message": 'Unauthorized',
                "statusCode": 401,
                "redirect": True
            }, status=401
        )

    return response