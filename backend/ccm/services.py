import logging
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from canvasapi import Canvas
from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager


logger = logging.getLogger(__name__)
course_manager = CanvasCredentialManager()

def create_sections(task):
    """
    Simply print the sections from the task.
    Args:
        task: Django-Q task object containing sections data
    """
    try:
        logger.info(f"Received raw task object for create sections: {task}")
        sections = task.get('sections', [])
        course_id = task.get('course_id')
        user_id = task.get('user_id')
        canvas_callback_url = task.get('canvas_callback_url')
        logger.info(f"Received course_id: {course_id}, user_id: {user_id}, canvas_callback_url: {canvas_callback_url}")

        logger.info(f"Received sections to create: {sections}")
        User = get_user_model()
        user = User.objects.get(pk=user_id)
        
        factory = RequestFactory()
        request = factory.get('/oauth/oauth-callback')
        request.user = user
        request.build_absolute_uri = lambda path: canvas_callback_url
        canvas_api: Canvas = course_manager.get_canvasapi_instance(request)
        course = canvas_api.get_course(course_id)
        for section_name in sections:
            section = course.create_course_section(course_section={"name": section_name})
            logger.info(f"Creating sections for course_id: {section}")
            
        return [{'name': name} for name in sections]
    except Exception as e:
        logger.error(f"Error in create_sections task: {str(e)}")
        raise