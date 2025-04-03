import os
from typing import List, Optional
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from http import HTTPStatus

def parse_csp(csp_key: str, extra_csp_sources: Optional[List[str]] = None) -> List[str]:
    """
    Parse CSP source from an environment variable.
    - If the variable is set, split its value by commas.
    """
    csp_value = os.getenv(csp_key, '').split(',')
    DEFAULT_CSP_VALUE = ["'self'"]
    
    if not any(csp_value):
        if extra_csp_sources is not None:
            return DEFAULT_CSP_VALUE + extra_csp_sources
        else:
            return DEFAULT_CSP_VALUE
    else:
        if extra_csp_sources is not None:
            return DEFAULT_CSP_VALUE + csp_value + extra_csp_sources
        else:
            return DEFAULT_CSP_VALUE + csp_value 

from rest_framework.views import exception_handler


# https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if isinstance(exc, APIException):
        return Response(
            {
                "message": str(exc),
                "status_code": exc.status_code if hasattr(exc, 'status_code') else HTTPStatus.INTERNAL_SERVER_ERROR,
                "redirect": True
            },
            status=exc.status_code if hasattr(exc, 'status_code') else HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return response
