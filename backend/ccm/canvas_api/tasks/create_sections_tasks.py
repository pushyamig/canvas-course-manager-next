import logging
from canvasapi import Canvas
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def create_celery_sections(access_token, url, course_id, section_names):
  course = Canvas(url, access_token).get_course(course_id)
  for section_name in section_names:
    section = course.create_course_section(course_section={"name": section_name})
    logger.info(f"Creating sections for course_id: {section}")



