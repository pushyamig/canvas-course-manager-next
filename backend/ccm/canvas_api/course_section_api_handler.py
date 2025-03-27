import logging, asyncio, time
from dataclasses import asdict
from http import HTTPStatus
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.request import Request

from canvasapi.exceptions import CanvasException
from canvasapi import Canvas

from backend.ccm.canvas_api.canvasapi_dataclasses import Section
from backend.ccm.canvas_api.canvasapi_serializer import CourseSectionSerializer
from .exceptions import CanvasHTTPError, SectionCreationError
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
            err_response: CanvasHTTPError = CanvasCredentialManager.handle_serializer_errors(serializer.errors, request.data)
            return Response(err_response.to_dict(), status=err_response.status_code)
        
        sections: list = serializer.validated_data['sections']
        sections = ['u1', '', 'u3', '']
        logger.info(f"Creating {sections} sections for course_id: {course_id}")
        try:
          canvas_api: Canvas = CANVAS_CREDENTIALS.get_canvasapi_instance(request)
        except InvalidOAuthReturnError as e:
          err_response: CanvasHTTPError = CANVAS_CREDENTIALS.handle_canvas_api_exception(e, request, str(course_id))
          return Response(err_response.to_dict(), status=err_response.status_code)
           
        
        start_time: float = time.perf_counter()
        results = asyncio.run(self.create_sections(canvas_api, course_id, sections))
        logger.info(f"Sections created: {results}")
        end_time: float = time.perf_counter()
        logger.info(f"Time taken to create {len(sections)} sections: {end_time - start_time:.2f} seconds")

        success_res = [asdict(result) for result in results if isinstance(result, Section)]
        error_res = [res.to_dict() for res in results if isinstance(res, SectionCreationError)]

        logger.info(f"Success: {success_res}")
        logger.info(f"Errors: {error_res}")
        if not error_res: # No errors
            return Response(success_res, status=HTTPStatus.CREATED)
        
        # error_list = [entry["error"] for entry in error_res]
        # CANVAS_CREDENTIALS.handle_revoked_token(error_list, request)
        
        partial_success = [
            CANVAS_CREDENTIALS.handle_canvas_api_exception(error_entry["error"], error_entry["section_name"]).to_dict()["errors"][0]
            for error_entry in error_res
        ]

        # Determine final status code dynamically
        status_codes = [error["canvasStatusCode"] for error in partial_success]
        final_status_code = HTTPStatus.BAD_GATEWAY if len(set(status_codes)) > 1 else status_codes[0]

        # If both successes and errors exist, return only the error response
        if success_res and partial_success:
            return Response({"statusCode": final_status_code, "errors": partial_success}, status=final_status_code)

        # If only errors exist, return the structured error response
        return Response({"statusCode": final_status_code, "errors": partial_success}, status=final_status_code)
            
        
    async def create_sections(self, canvas_api, course_id, section_names):
        """Creates multiple sections concurrently."""
        tasks = [self.create_section(canvas_api, course_id, name) for name in section_names]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def create_section_sync(self, canvas_api: Canvas, course_id: int, section_name: str):
        """Creates a section synchronously with automatic retry handling."""
        try:
            logger.info(f"Creating section: {section_name} for course_id: {course_id} at {time.strftime('%H:%M:%S')}")
            section = canvas_api.get_course(course_id).create_course_section(course_section={"name": section_name})
            return Section(
              id=section.id,
              name=section.name,
              course_id=section.course_id,
              nonxlist_course_id=section.nonxlist_course_id
)
        except (CanvasException, Exception) as e:
            raise SectionCreationError(section_name, e)

    async def create_section(self, canvas_api: Canvas, course_id: int, section_name: str):
        """Async wrapper to call create_section_sync using asyncio.to_thread()."""
        try:
            return await asyncio.to_thread(self.create_section_sync, canvas_api, course_id, section_name)
        except Exception as e:
          return e if isinstance(e, SectionCreationError) else SectionCreationError(section_name, e)
