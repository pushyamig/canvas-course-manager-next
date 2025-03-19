from backend.ccm.canvas_api.course_api_handler import CanvasCourseAPIHandler
from backend.ccm.canvas_api.course_section_api_handler import CanvasCourseSectionsAPIHandler
from django.urls import path

urlpatterns = [
  path('course/<int:course_id>/', CanvasCourseAPIHandler.as_view(), name='course'),
  path('course/<int:course_id>/sections/', CanvasCourseSectionsAPIHandler.as_view(), name='course_sections'),
]