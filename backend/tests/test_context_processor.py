from django.test import SimpleTestCase, RequestFactory
from unittest.mock import patch, MagicMock
from django.conf import settings
from backend.ccm.context_processors import ccm_globals, _get_flatpage_content, _candidate_urls

class CCMGlobalsTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.session = {
            'course': {
                'id': 40001,
                'roles': ['TeacherEnrollment', 'Account Admin']
            }
        }

    @patch('backend.ccm.context_processors.GlobalsUserSerializer')
    @patch('backend.ccm.context_processors.CanvasOAuth2Token.objects.filter')
    @patch('backend.ccm.context_processors._get_flatpage_content')
    def test_ccm_globals_authenticated_user(self, mock_get_flatpage_content, mock_canvas_oauth_filter, mock_globals_user_serializer):
        mock_get_flatpage_content.side_effect = ['', '']
        mock_user = MagicMock(is_authenticated=True)
        self.request.user = mock_user

        mock_globals_user_serializer.return_value.data = {
            'loginId': 'jdoe',
            'isStaff': True
        }
        mock_canvas_oauth_filter.return_value.exists.return_value = True

        context = ccm_globals(self.request)

        self.assertEqual(context['ccm_globals']['environment'], 'development' if settings.DEBUGPY_ENABLE else 'production')
        self.assertEqual(context['ccm_globals']['canvasURL'], f"https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}")
        self.assertEqual(context['ccm_globals']['user']['loginId'], 'jdoe')
        self.assertEqual(context['ccm_globals']['user']['isStaff'], True)
        self.assertEqual(context['ccm_globals']['user']['hasCanvasToken'], True)
        self.assertEqual(context['ccm_globals']['userLoginID'], 'jdoe')
        self.assertEqual(context['ccm_globals']['course']['id'], 40001)
        self.assertEqual(context['ccm_globals']['course']['roles'], ['TeacherEnrollment', 'Account Admin'])
        self.assertEqual(context['ccm_globals']['baseHelpURL'], settings.HELP_URL)
        self.assertEqual(context['ccm_globals']['googleAnalyticsId'], settings.GOOGLE_ANALYTICS_ID)
        self.assertEqual(context['ccm_globals']['umConsentManagerScriptUrl'], settings.UM_CONSENT_MANAGER_SCRIPT_URL)

    @patch('backend.ccm.context_processors.GlobalsUserSerializer')
    @patch('backend.ccm.context_processors.CanvasOAuth2Token.objects.filter')
    @patch('backend.ccm.context_processors._get_flatpage_content')
    def test_ccm_globals_includes_banner_footer_html(self, mock_get_flatpage_content, mock_canvas_oauth_filter, mock_globals_user_serializer):
        mock_user = MagicMock(is_authenticated=True)
        self.request.user = mock_user

        mock_globals_user_serializer.return_value.data = {'loginId': 'jdoe'}
        mock_canvas_oauth_filter.return_value.exists.return_value = True
        mock_get_flatpage_content.side_effect = [
            '<a href="/courses/{{course_id}}/settings">Banner</a>',
            '<div>Footer</div>',
        ]

        context = ccm_globals(self.request)

        self.assertEqual(context['banner_html'], '<a href="/courses/40001/settings">Banner</a>')
        self.assertEqual(context['footer_html'], '<div>Footer</div>')

    @patch('backend.ccm.context_processors.GlobalsUserSerializer')
    @patch('backend.ccm.context_processors.CanvasOAuth2Token.objects.filter')
    @patch('backend.ccm.context_processors._get_flatpage_content')
    def test_ccm_globals_empty_banner_footer_when_missing(self, mock_get_flatpage_content, mock_canvas_oauth_filter, mock_globals_user_serializer):
        mock_user = MagicMock(is_authenticated=True)
        self.request.user = mock_user

        mock_globals_user_serializer.return_value.data = {'loginId': 'jdoe'}
        mock_canvas_oauth_filter.return_value.exists.return_value = False
        mock_get_flatpage_content.side_effect = ['', '']

        context = ccm_globals(self.request)

        self.assertEqual(context['banner_html'], '')
        self.assertEqual(context['footer_html'], '')

    @patch('backend.ccm.context_processors.Site.objects.get_current')
    @patch('backend.ccm.context_processors.FlatPage.objects.get')
    @patch('backend.ccm.context_processors.FlatPage.objects.filter')
    def test_get_flatpage_content_fallbacks_to_url_lookup(self, mock_filter, mock_get, mock_get_current_site):
        mock_get_current_site.side_effect = Exception('site lookup failed')
        mock_get.side_effect = Exception('site-bound lookup failed')
        mock_filter.return_value.first.return_value = MagicMock(content='<div>Banner</div>')

        content = _get_flatpage_content(self.request, '/banner/')

        self.assertEqual(content, '<div>Banner</div>')

    @patch('backend.ccm.context_processors.Site.objects.get_current')
    @patch('backend.ccm.context_processors.FlatPage.objects.get')
    @patch('backend.ccm.context_processors.FlatPage.objects.filter')
    def test_get_flatpage_content_returns_empty_when_not_found(self, mock_filter, mock_get, mock_get_current_site):
        mock_get_current_site.side_effect = Exception('site lookup failed')
        mock_get.side_effect = Exception('site-bound lookup failed')
        mock_filter.return_value.first.return_value = None

        content = _get_flatpage_content(self.request, '/banner/')

        self.assertEqual(content, '')

    def test_candidate_urls_supports_trailing_and_non_trailing_slash(self):
        self.assertEqual(_candidate_urls('/banner/'), ['/banner/', '/banner'])
        self.assertEqual(_candidate_urls('/banner'), ['/banner/', '/banner'])
