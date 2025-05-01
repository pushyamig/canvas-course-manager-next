import os
from typing import List, Optional

def parse_csp(csp_key: str, extra_csp_sources: Optional[List[str]] = None) -> List[str]:
    """
    Parse CSP source from an environment variable.
    - If the variable is set, split its value by commas.
    """
    csp_value = os.getenv(csp_key, '').split(',')
    DEFAULT_CSP_VALUE = ["'self'"]
    
    if not any(csp_value):
        if extra_csp_sources is not None:
            return DEFAULT_CSP_VALUE + extra_csp_sources
        else:
            return DEFAULT_CSP_VALUE
    else:
        if extra_csp_sources is not None:
            return DEFAULT_CSP_VALUE + csp_value + extra_csp_sources
        else:
            return DEFAULT_CSP_VALUE + csp_value 

from django.core.mail import send_mail

def send_task_completion_email(to_email, section_id, results):
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed = [r for r in results if r['status'] == 'failed']

    body = f"""
    Enrollment to section {section_id} completed.
    ✅ Success: {success_count}
    ❌ Failed: {len(failed)}

    Failed Users:
    {chr(10).join([f"{r['user']}: {r['error']}" for r in failed])}
    """

    send_mail(
        subject='Canvas Enrollment Task Complete',
        message=body,
        from_email='noreply@yourdomain.com',
        recipient_list=[to_email],
    )