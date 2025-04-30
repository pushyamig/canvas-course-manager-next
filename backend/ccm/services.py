import logging

logger = logging.getLogger(__name__)

def create_sections(task):
    """
    Simply print the sections from the task.
    Args:
        task: Django-Q task object containing sections data
    """
    try:
        logger.info(f"Received raw task object: {task}")
        sections = task.get('sections', [])
        logger.info(f"Received sections to create: {sections}")
        
        for section_name in sections:
            logger.info(f"Would create section: {section_name}")
            
        return [{'name': name} for name in sections]
    except Exception as e:
        logger.error(f"Error in create_sections task: {str(e)}")
        raise