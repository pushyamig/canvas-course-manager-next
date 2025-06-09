import logging
from http import HTTPStatus
from canvasapi import Canvas
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.response import Response
from rest_framework.request import Request

from canvasapi.exceptions import CanvasException
from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager
from backend.ccm.canvas_api.canvasapi_serializer import CanvasObjectROSerializer
from backend.ccm.canvas_api.course_section_api_handler import CanvasCourseSectionAPIHandler
from backend.ccm.canvas_api.exceptions import CanvasErrorHandler, HTTPAPIError

logger = logging.getLogger(__name__)

class CanvasAdminSectionsAPIHandler(LoggingMixin, APIView):
    """
    API handler for "merge-able" sections data for users with admin access
    """
    logging_methods = ['GET']
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    courses_allowed_fields = {"id"}

    def __init__(self, credential_manager=None):
        self.credential_manager = credential_manager or CanvasCredentialManager()
        self.canvas_error = CanvasErrorHandler()
        super().__init__()

    def get(self, request: Request) -> Response:
        """
        Get sections data from Canvas for admins.
        """
        term_id = request.query_params.get('term_id', None)
        instructor_name = request.query_params.get('instructor_name', None)
        course_name = request.query_params.get('course_name', None)


        if not term_id:
            return Response({"error": "Term ID is required as a parameter"}, status=HTTPStatus.BAD_REQUEST)
        
        if not ((instructor_name != None) ^ (course_name != None)): # XOR condition ensures one, but not both, is provided
            return Response({"error": "Provide either 'instructor_name' or 'course_name' as a parameter. Both cannot be provided together."},
                            status=HTTPStatus.BAD_REQUEST)
        
        canvas_api: Canvas = self.credential_manager.get_canvasapi_instance(request)
        try:
            # Get accounts accessible to the admin user
            logger.info(f"Retrieving admin sections data for term_id: {term_id}")
            accounts = canvas_api.get_accounts()
            if not accounts:
                logger.info("No accounts found that the current API user can view or manage.")
                logger.info("This is common for non-admin users (e.g., students, teachers).")
                return []
            viewable_accounts = []
            for account in accounts:
            # Each 'account' object returned by get_accounts() will have 'id' and 'name' attributes.
                viewable_accounts.append({'id': account.id, 'name': account.name})
                logger.info(f"  Found account: {account.name} (ID: {account.id})")

            accounts_serializer = CanvasObjectROSerializer(accounts, allowed_fields={'id','parent_account_id'})
            accounts_data = accounts_serializer.data
            ## ^ STUCK HERE: EMPTY DATA RETURNED "[]", need to set admin access?

            account_id_set = { account.get('id') for account in accounts_data }
            filtered_account_ids = [
                account.get('id') for account in accounts_data if 
                    account.get('parent_account_id') is None # account is the root account
                    or not(account.get('parent_account_id') in account_id_set) # subaccount of a separate account
            ]
            logger.info(f"Found {len(filtered_account_ids)} of {len(accounts_data)} accounts accessible to the admin user.")

            # build term and search parameters for course search
            queryParams = {
                'state': ['created', 'claimed', 'available'],
                'enrollment_term_id': term_id,
                'per_page': 100,
            }
            if instructor_name:
                queryParams['by_teachers'] = ['sis_login_id:' + instructor_name]
                logger.info(f"Searching for courses with instructor name: {instructor_name}")
            if course_name:
                queryParams['search_term'] = course_name
                logger.info(f"Searching for courses with name: {course_name}")

            # Get courses for filtered accounts
            filtered_accounts_courses = []
            for account_id in filtered_account_ids:
                logger.info(f"Retrieving courses for account_id: {account_id}")
                courses = canvas_api.get_account(account_id).get_courses(**queryParams)
                courses_serializer = CanvasObjectROSerializer(courses, allowed_fields=self.courses_allowed_fields, many=True)
                courses_data = courses_serializer.data
                filtered_accounts_courses.extend(courses_data)

            #TODO: nest these requests under the account_id loop
            for course in filtered_accounts_courses:
                logger.info(f"Getting sections for course with id: {course.get('id')}")
                course_id = course.get('id')
                if course_id:
                    # Retrieve sections for each course
                    sections = CanvasCourseSectionAPIHandler.retrieve_sections_from_course_id(
                        canvas_api,
                        course_id,
                        course_section_allowed_fields=CanvasCourseSectionAPIHandler.course_section_allowed_fields,
                        include=['total_students']
                    )
                    course['sections'] = sections
            return Response(filtered_accounts_courses, status=HTTPStatus.OK)
        except (CanvasException, Exception) as e:
            self.canvas_error.handle_canvas_api_exceptions(HTTPAPIError(str(request.data), e))
            return Response(self.canvas_error.to_dict(), status=self.canvas_error.to_dict().get('statusCode'))
