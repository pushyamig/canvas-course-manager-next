import logging, asyncio
from http import HTTPStatus
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.request import Request

from canvasapi.exceptions import CanvasException
from canvasapi.course import Course
from canvasapi import Canvas

from backend.ccm.canvas_api.canvasapi_serializer import CourseSectionSerializer, CourseSerializer
from .exceptions import CanvasHTTPError
from canvas_oauth.exceptions import InvalidOAuthReturnError

from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager

from drf_spectacular.utils import extend_schema

from rest_framework_tracking.mixins import LoggingMixin

logger = logging.getLogger(__name__)

CANVAS_CREDENTIALS = CanvasCredentialManager()

class CanvasCourseAPIHandler(LoggingMixin, APIView):

    logging_methods = ['GET', 'PUT']
    """
    API handler for Canvas course data.
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseSerializer  # Ensures Swagger UI recognizes it

    def get(self, request: Request, course_id: int) -> Response:
        """
        Get course data from Canvas.
        """
        try:
            canvas_api: Canvas = CANVAS_CREDENTIALS.get_canvasapi_instance(request)
            logger.info(f"Getting course data for course_id: {course_id}")
            
            # Call the Canvas API package to get course details.
            course: Course = canvas_api.get_course(course_id)
            logger.info(f"Course data retrieved: {course}")
            
            # Format the course object to return specific course info
            formatted_course = {
                "id": course.id,
                "name": course.name,
                "enrollment_term_id": course.enrollment_term_id
            }
            
            return Response(formatted_course, status=HTTPStatus.OK)
        except (CanvasException, InvalidOAuthReturnError, Exception) as e:
            err_response: CanvasHTTPError = CANVAS_CREDENTIALS.handle_canvas_api_exception(e, request, str(course_id))
            return Response(err_response.to_dict(), status=err_response.status_code)
      
    @extend_schema(
        operation_id="update_course",
        summary="Change Course name and code",
        description="Update the details of a specific course. Only Name and Course Code can be updated with same name.",
        request=CourseSerializer,
    )
    def put(self, request: Request, course_id: int) -> Response:
        # Validate the incoming data using the serializer.
        serializer = CourseSerializer(data=request.data)
        if not serializer.is_valid():
            err_response: CanvasHTTPError = CanvasCredentialManager.handle_serializer_errors(serializer.errors, request.data)
            return Response(err_response.to_dict(), status=err_response.status_code)

        update_data = serializer.validated_data
        try:
            canvas_api: Canvas = CANVAS_CREDENTIALS.get_canvasapi_instance(request)
            # Get the course instance
            course: Course = canvas_api.get_course(course_id)
            # Call the update method on the course instance
            put_course_res: str= course.update(course={'name': update_data.get("newName"), 'course_code': update_data.get("newName")})
            formatted_course = {'id': course.id, 'name': put_course_res, 'enrollment_term_id': course.enrollment_term_id }
            return Response(formatted_course, status=HTTPStatus.OK)
        except (CanvasException, InvalidOAuthReturnError, Exception) as e:
            err_response: CanvasHTTPError = CANVAS_CREDENTIALS.handle_canvas_api_exception(e, request, str(request.data))
            return Response(err_response.to_dict(), status=err_response.status_code)

class CanvasCourseSectionsAPIHandler(LoggingMixin, APIView):
    logging_methods = ['POST']
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        operation_id="create_course_sections",
        summary="create Course sections",
        description="This handle course sections creation upto 60 sections.",
        request=CourseSectionSerializer,
    )
    def post(self, request: Request, course_id: int) -> Response:
        serializer = CourseSectionSerializer(data=request.data)
        if serializer.is_valid():
            sections = serializer.validated_data['sections']
            try:
                canvas_api: Canvas = CANVAS_CREDENTIALS.get_canvasapi_instance(request)
                 # Run section creation in parallel using asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self.create_sections(canvas_api, course_id, sections))
                
                return Response(results, status=HTTPStatus.CREATED)
                # created_sections = []
                # for section_name in sections:
                #     section = canvas_api.get_course(course_id).create_course_section(course_section={'name': section_name})
                #     created_sections.append({
                #         'name': section.name
                #     })
                # return Response(created_sections, status=HTTPStatus.CREATED)
            except CanvasException as e:
                logger.error(f"Canvas API error: {e}")
                err_response: CanvasHTTPError = CANVAS_CREDENTIALS.handle_canvas_api_exception(e, request, str(course_id))
                return Response(err_response.to_dict(), status=err_response.status_code)
            except InvalidOAuthReturnError as e:
                err_response: CanvasHTTPError = CanvasHTTPError(str(e), HTTPStatus.FORBIDDEN.value, str(course_id))
                return Response(err_response.to_dict(), status=err_response.status_code)
        else:
            logger.error(f"Serializer error: {serializer.errors}")
            err_response: CanvasHTTPError = CanvasHTTPError(serializer.errors, HTTPStatus.BAD_REQUEST.value, str(request.data))
            return Response(err_response.to_dict(), status=err_response.status_code)
        
    async def create_sections(self, canvas_api, course_id, section_names):
        """Creates multiple sections concurrently."""
        tasks = [self.create_section(canvas_api, course_id, name) for name in section_names]
        return await asyncio.gather(*tasks)

    def create_section_sync(self, canvas_api: Canvas, course_id: int, section_name: str):
        """Creates a section synchronously with automatic retry handling."""
        section = canvas_api.get_course(course_id).create_course_section(course_section={"name": section_name})
        return {"name": section.name, "status": "Created"}

    async def create_section(self, canvas_api: Canvas, course_id: int, section_name: str):
        """Async wrapper to call create_section_sync using asyncio.to_thread()."""
        try:
            return await asyncio.to_thread(self.create_section_sync, canvas_api, course_id, section_name)
        except Exception as e:
            return {"name": section_name, "status": "Failed", "error": str(e)}

