
import logging, asyncio
import time
from http import HTTPStatus
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.request import Request

from canvasapi.exceptions import CanvasException
from canvasapi import Canvas

from backend.ccm.canvas_api.canvasapi_serializer import CourseSectionSerializer
from .exceptions import CanvasHTTPError
from canvas_oauth.exceptions import InvalidOAuthReturnError

from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager

from drf_spectacular.utils import extend_schema

from rest_framework_tracking.mixins import LoggingMixin

logger = logging.getLogger(__name__)

CANVAS_CREDENTIALS = CanvasCredentialManager()

class CanvasCourseSectionsAPIHandler(LoggingMixin, APIView):
    logging_methods = ['POST']
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseSectionSerializer

    @extend_schema(
        operation_id="create_course_sections",
        summary="create Course sections",
        description="This handle course sections creation upto 60 sections.",
        request=CourseSectionSerializer,
    )
    def post(self, request: Request, course_id: int) -> Response:
        serializer: CourseSectionSerializer = CourseSectionSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer error: {serializer.errors}")
            err_response: CanvasHTTPError = CanvasHTTPError(serializer.errors, HTTPStatus.BAD_REQUEST.value, str(request.data))
            return Response(err_response.to_dict(), status=err_response.status_code)
        
        sections: list = serializer.validated_data['sections']
        sections = ['u1', '', 'u3']
        logger.info(f"Creating {sections} sections for course_id: {course_id}")
        canvas_api: Canvas = CANVAS_CREDENTIALS.get_canvasapi_instance(request)
        
        start_time: float = time.perf_counter()
        results = asyncio.run(self.create_sections(canvas_api, course_id, sections))
        logger.info(f"Sections created: {results}")
        end_time: float = time.perf_counter()
        logger.info(f"Time taken to create {len(sections)} sections: {end_time - start_time:.2f} seconds")

        success_res = [result for result in results if not isinstance(result, dict)]
        error_res = [result for result in results if isinstance(result, Exception)]
        
        return Response(results, status=HTTPStatus.CREATED)
            
        
    async def create_sections(self, canvas_api, course_id, section_names):
        """Creates multiple sections concurrently."""
        tasks = [self.create_section(canvas_api, course_id, name) for name in section_names]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def create_section_sync(self, canvas_api: Canvas, course_id: int, section_name: str):
        """Creates a section synchronously with automatic retry handling."""
        try:
            logger.info(f"Creating section: {section_name} for course_id: {course_id} at {time.strftime('%H:%M:%S')}")
            section = canvas_api.get_course(course_id).create_course_section(course_section={"name": section_name})
            return {
                "id": section.id,
                "name": section.name,
                "course_id": section.course_id,
                "nonxlist_course_id": section.nonxlist_course_id,
                "total_students": 0
            }
        except (CanvasException, InvalidOAuthReturnError, Exception) as e:
            logger.error(f"Error creating section: {e}")
            raise e

    async def create_section(self, canvas_api: Canvas, course_id: int, section_name: str):
        """Async wrapper to call create_section_sync using asyncio.to_thread()."""
        try:
            return await asyncio.to_thread(self.create_section_sync, canvas_api, course_id, section_name)
        except (CanvasException, InvalidOAuthReturnError, Exception) as e:
            logger.error(f"Error creating section: {e}")
            raise e

