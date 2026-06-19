from typing import Any, Dict, Optional, Union

from django.conf import settings
from django.http import HttpRequest
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site

from .serializer import GlobalsUserSerializer
from canvas_oauth.models import CanvasOAuth2Token


def _candidate_urls(url: str) -> list[str]:
    normalized = url.strip() or '/'
    if not normalized.startswith('/'):
        normalized = f'/{normalized}'
    if normalized == '/':
        return ['/']

    slash = normalized if normalized.endswith('/') else f'{normalized}/'
    no_slash = normalized.rstrip('/')

    candidates: list[str] = []
    for candidate in (slash, no_slash):
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _get_flatpage_content(request: HttpRequest, url: str) -> str:
    """
    Return flatpage HTML for the current site and URL, or empty string when unavailable.
    """
    urls = _candidate_urls(url)

    try:
        site = Site.objects.get_current(request)
        for candidate_url in urls:
            page = FlatPage.objects.filter(url=candidate_url, sites=site).first()
            if page and page.content:
                return page.content
    except Exception:
        pass

    try:
        # Fallback to URL-only lookup to avoid silent misses when Site mapping is not configured.
        for candidate_url in urls:
            page = FlatPage.objects.filter(url=candidate_url).first()
            if page and page.content:
                return page.content
    except Exception:
        pass

    return ""


def _substitute_course_id_token(content: str, request: HttpRequest) -> str:
    course_data = request.session.get('course') if hasattr(request, 'session') else None
    course_id = course_data.get('id') if isinstance(course_data, dict) else None
    return content.replace('{{course_id}}', str(course_id) if course_id is not None else '')


def ccm_globals(request: HttpRequest) -> Dict[str, Union[str, Dict[str, Any], None]]:
    user_data: Optional[Dict[str, Any]] = GlobalsUserSerializer(request.user).data if request.user.is_authenticated else None
    if user_data:
        user_data['hasCanvasToken'] = CanvasOAuth2Token.objects.filter(user=request.user).exists()
        userLoginID: Optional[str] = user_data.get('loginId')  # Get the value from user_data['loginId']
    else:
        userLoginID = None
    # Access the course data from the session
    course_data: Optional[Dict[str, Any]] = request.session.get('course', None)
    print(f"Course data in context processor: {course_data}")  # Debug print to verify course data is available
    banner_content = _substitute_course_id_token(_get_flatpage_content(request, '/banner/'), request)
    footer_content = _substitute_course_id_token(_get_flatpage_content(request, '/footer/'), request)

    return {
        'banner_html': banner_content,
        'footer_html': footer_content,
        'ccm_globals': {
            'environment': 'development' if settings.DEBUGPY_ENABLE else 'production',
            'canvasURL': f"https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}",
            'user': user_data,
            'userLoginID': userLoginID,  # Add userLoginID to the globals
            'course': course_data,
            'baseHelpURL': settings.HELP_URL,
            'googleAnalyticsId': settings.GOOGLE_ANALYTICS_ID,
            'umConsentManagerScriptUrl': settings.UM_CONSENT_MANAGER_SCRIPT_URL,
        }
    }
