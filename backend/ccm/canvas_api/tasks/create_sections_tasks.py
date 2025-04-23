import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def create_celery_sections(sections):
  logger.info(f"Creating sections with Celery and: {sections}")



