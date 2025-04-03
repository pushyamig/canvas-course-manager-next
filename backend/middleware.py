import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class TokenValidationMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        # Check if the response status is 401
        if response.status_code == 401:
            logger.info("Unauthorized access detected. Modifying response.")
            return JsonResponse({'statusCode': 401, 'message': 'Unauthorized', 'redirect': True}, status=401)
        
        # Log the response for debugging purposes
        logger.info(f"Response status: {response.status_code}")
        
        # Return the original response if status is not 401
        return response