import logging
from canvasapi import Canvas
from celery import shared_task
from django.test import RequestFactory
from django.contrib.auth import get_user_model

from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager

logger = logging.getLogger(__name__)

course_manager = CanvasCredentialManager()

@shared_task
def create_celery_sections(user_id, url, course_id, section_names):
   logger.info(user_id)
   logger.info(url)
   User = get_user_model()
   user = User.objects.get(pk=user_id)
   logger.info(f"User: {user.first_name}")
   factory = RequestFactory()
   request = factory.get('/oauth/oauth-callback')
   request.user = user
   request.build_absolute_uri = lambda path: url
   canvas_api: Canvas = course_manager.get_canvasapi_instance(request)
   course = canvas_api.get_course(course_id)
   for section_name in section_names:
      section = course.create_course_section(course_section={"name": section_name})
      logger.info(f"Creating sections for course_id: {section}")



