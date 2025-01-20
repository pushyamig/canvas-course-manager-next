import random, logging, string
from typing import Dict, List, Any
from django.contrib.auth import login as ccm_user_login
from django.conf import settings
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from lti_tool.views import LtiLaunchBaseView
from pylti1p3.exception import LtiException
from django.contrib.auth.models import User
from django.shortcuts import redirect


logger = logging.getLogger(__name__)

class LTILaunchError(Exception):
    """
    Exception class for errors that occur while processing data from the LTI launch
    """


class CCMLTILaunchView(LtiLaunchBaseView):

    LTI_CUSTOM_PARAMS: List[str] = ['roles', 'is_root_account_admin', 'login_id', 'course_id']
    LTI_CUSTOM_PARAMS_URL: str = 'https://purl.imsglobal.org/spec/lti/claim/custom'
    
    def validate_custom_lti_launch_data(self, lti_launch: Dict[str, Any]) -> None:
        if self.LTI_CUSTOM_PARAMS_URL not in lti_launch:
            raise LTILaunchError(
                'You need to have custom parameters configured on your LTI Launch. ' +
                'Please see the LTI installation guide in README for more information.'
            )
        
        custom_data: Dict[str, Any] = lti_launch[self.LTI_CUSTOM_PARAMS_URL]
        missing_keys: List[str] = [key for key in self.LTI_CUSTOM_PARAMS if key not in custom_data]
        if missing_keys:
            raise LTILaunchError(f"LTI custom variables `{', '.join(missing_keys)}` are missing in the `{self.LTI_CUSTOM_PARAMS_URL}` ")
    
    def login_user_from_lti(self, request: HttpRequest, launch_data: Dict[str, Any]) -> None:
        course_id: str = launch_data[self.LTI_CUSTOM_PARAMS_URL].get('course_id')
        login_id: str = launch_data[self.LTI_CUSTOM_PARAMS_URL].get('login_id')
        roles: str = launch_data[self.LTI_CUSTOM_PARAMS_URL].get('roles')
        roles_list: List[str] = roles.split(',') if roles else []

        email: str = launch_data.get('email')
        first_name: str = launch_data.get('given_name')
        last_name: str = launch_data.get('family_name')
        try:
            username: str = login_id
            logger.info(f'User {first_name} {last_name} {email} {username} launched the tool')
            user_obj: User = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning(f'user {username} never logged into the app, hence creating the user')
            password: str = ''.join(random.sample(string.ascii_letters, settings.RANDOM_PASSWORD_DEFAULT_LENGTH))
            user_obj = User.objects.create_user(username=username, email=email, password=password, first_name=first_name,
                                                last_name=last_name)
        except Exception as e:
            raise LTILaunchError(f'Error occured while getting the user info from LTI launch data due to {e}')
            
        try: 
            ccm_user_login(request, user_obj)
        except (ValueError, TypeError, Exception) as e:
            raise LTILaunchError(f'Logging user after LTI launch failed due to {e}')
        
        if course_id is not None:
            try:
                course_id_int: int = int(course_id)
            except ValueError:
                raise LTILaunchError(f'Course ID from LTI launch cannot be converted to an integer. Value: {course_id}')

            request.session['course'] = {
                'id': course_id_int,
                'roles': roles_list,
            }
        else:
            raise LTILaunchError(f'Course ID from LTI launch cannot be null.')
    
    def handle_resource_launch(self, request: HttpRequest, lti_launch: Any) -> HttpResponseRedirect:
        try:
            launch_data: Dict[str, Any] = lti_launch.get_launch_data()
            self.validate_custom_lti_launch_data(launch_data)
            self.login_user_from_lti(request, launch_data)
        except (LtiException, LTILaunchError, Exception) as e:
            logger.error(e)
            response: HttpResponse = HttpResponse(e)
            response.status_code = 401
            return response 
        return redirect(reverse('home'))
