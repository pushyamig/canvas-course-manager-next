import logging
from http import HTTPStatus
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.request import Request

from canvasapi.exceptions import CanvasException
from canvasapi.course import Course
from canvasapi import Canvas
from rest_framework.serializers import Serializer

from backend.ccm.canvas_api.canvasapi_serializer import CanvasObjectROSerializer, CourseSerializer
from .exceptions import CanvasHTTPError, HTTPAPIError

from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager

from drf_spectacular.utils import extend_schema

from rest_framework_tracking.mixins import LoggingMixin

logger = logging.getLogger(__name__)

# CANVAS_CREDENTIALS = CanvasCredentialManager()

class CanvasCourseAPIHandler(LoggingMixin, APIView):

    logging_methods = ['GET', 'PUT']
    course_allowed_fields = {"id", "name", "enrollment_term_id"}
    """
    API handler for Canvas course data.
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseSerializer  # Ensures Swagger UI recognizes it

    def __init__(self, credential_manager=None):
        self.credential_manager = credential_manager or CanvasCredentialManager()
        super().__init__()

    def get(self, request: Request, course_id: int) -> Response:
        """
        Get course data from Canvas.
        """
        logger.info(f"Getting course data for course_id: {course_id}")

        canvas_api: Canvas = self.credential_manager.get_canvasapi_instance(request)
        
        try:
            course: Course = canvas_api.get_course(course_id)
            serializer = CanvasObjectROSerializer(course, allowed_fields=self.course_allowed_fields)
            return Response(serializer.data, status=HTTPStatus.OK)
        
        except (CanvasException, Exception) as e:
            err_response: CanvasHTTPError = self.credential_manager.handle_canvas_api_exceptions(HTTPAPIError(str(course_id), e))
            return Response(err_response.to_dict(), status=err_response.to_dict().get('statusCode'))
      
    @extend_schema(
        operation_id="update_course",
        summary="Change Course name and code",
        description="Update the details of a specific course. Only Name and Course Code can be updated with same name.",
        request=CourseSerializer,
    )
    def put(self, request: Request, course_id: int) -> Response:
        logger.info(f"Updating course name: {course_id}")

        serializer: Serializer = CourseSerializer(data=request.data)
        if not serializer.is_valid():
            err_response: CanvasHTTPError = self.credential_manager.handle_serializer_errors(serializer.errors, request.data)
            return Response(err_response.to_dict(), status=err_response.to_dict().get('statusCode'))
        update_data = serializer.validated_data
        
        canvas_api: Canvas = self.credential_manager.get_canvasapi_instance(request)
        try:
            # Get the course instance
            course: Course = canvas_api.get_course(course_id)
            # Call the update method on the course instance
            put_course_res: str= course.update(course={'name': update_data.get("newName"), 'course_code': update_data.get("newName")})
            formatted_course = {'id': course.id, 'name': put_course_res, 'enrollment_term_id': course.enrollment_term_id }
            return Response(formatted_course, status=HTTPStatus.OK)
        
        except (CanvasException, Exception) as e:
            err_response: CanvasHTTPError = self.credential_manager.handle_canvas_api_exceptions(HTTPAPIError(str(course_id), e))
            return Response(err_response.to_dict(), status=err_response.to_dict().get('statusCode'))
