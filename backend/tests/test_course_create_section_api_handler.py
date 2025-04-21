import unittest
from unittest.mock import MagicMock, patch
from http import HTTPStatus

from rest_framework.test import APIRequestFactory

from backend.ccm.canvas_api.course_section_api_handler import CourseSectionAPIHandler
from backend.ccm.canvas_api.canvas_credential_manager import CanvasCredentialManager
from backend.ccm.canvas_api.exceptions import CanvasErrorHandler


class TestCourseSectionAPIHandler(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.credential_manager = MagicMock(spec=CanvasCredentialManager)
        self.mock_canvas_error_handler = MagicMock(spec=CanvasErrorHandler)
        self.api_handler = CourseSectionAPIHandler(credential_manager=self.credential_manager)
        
        # Mock Canvas API instance
        self.canvas_api = MagicMock()
        self.credential_manager.get_canvasapi_instance.return_value = self.canvas_api
        
        # Mock course
        self.course = MagicMock()
        self.canvas_api.get_course.return_value = self.course
        
        # Test data
        self.course_id = 12345
        self.section_names = ["Section A", "Section B", "Section C"]
        
    @patch('backend.ccm.canvas_api.course_section_api_handler.asyncio.to_thread')
    @patch('backend.ccm.canvas_api.course_section_api_handler.time.perf_counter')
    def test_create_sections_happy_path(self, mock_perf_counter, mock_to_thread):
        """Test successful concurrent creation of multiple sections."""
        # Configure perf_counter mock to return fixed float values
        mock_perf_counter.side_effect = [100.0, 100.5]  # start_time, end_time
        
        # Create request with section data
        request_data = {"sections": self.section_names}
        request = self.factory.post(
            f'/api/canvas/courses/{self.course_id}/sections', 
            data=request_data,
            format='json'
        )
        request.data = request_data
        
        # Mock serializer validation
        with patch('backend.ccm.canvas_api.course_section_api_handler.CourseSectionSerializer') as mock_serializer_class:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.validated_data = request_data
            mock_serializer_class.return_value = mock_serializer
            
            # Mock section creation results
            section_results = []
            for i, name in enumerate(self.section_names):
                section_result = {
                    "id": 1000 + i,
                    "name": name,
                    "course_id": self.course_id,
                    "total_students": 0
                }
                section_results.append(section_result)
            
            # Configure to_thread mock to return section results
            async def mock_async_result(func, *args, **kwargs):
                # Find the section name from args
                section_name = args[2]  # Third argument to create_section_sync
                # Find the corresponding result
                for result in section_results:
                    if result["name"] == section_name:
                        return result
                return None
                
            mock_to_thread.side_effect = mock_async_result
            
            # Execute the API call
            response = self.api_handler.post(request, self.course_id)
            
            # Verify response
            self.assertEqual(response.status_code, HTTPStatus.CREATED)
            self.assertEqual(len(response.data), len(self.section_names))
            
            # Verify each section was created with correct data
            for i, section_name in enumerate(self.section_names):
                self.assertEqual(response.data[i]["name"], section_name)
                self.assertEqual(response.data[i]["course_id"], self.course_id)
                
            # Verify concurrency - to_thread should be called for each section
            self.assertEqual(mock_to_thread.call_count, len(self.section_names))
            
    @patch('backend.ccm.canvas_api.course_section_api_handler.asyncio.run')
    def test_create_sections_with_real_async(self, mock_asyncio_run):
        """Test that asyncio.run is called with create_sections."""
        # Create request with section data
        request_data = {"sections": self.section_names}
        request = self.factory.post(
            f'/api/canvas/courses/{self.course_id}/sections', 
            data=request_data,  # Add data= explicitly
            format='json'
        )
        request.data = request_data  # Also set data attribute directly
        
        # Mock serializer validation
        with patch('backend.ccm.canvas_api.course_section_api_handler.CourseSectionSerializer') as mock_serializer_class:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.validated_data = request_data
            mock_serializer_class.return_value = mock_serializer
            
            # Mock the result of asyncio.run
            mock_asyncio_run.return_value = [
                {"id": 1001, "name": "Section A", "course_id": self.course_id, "total_students": 0},
                {"id": 1002, "name": "Section B", "course_id": self.course_id, "total_students": 0},
                {"id": 1003, "name": "Section C", "course_id": self.course_id, "total_students": 0}
            ]
            
            # Execute the API call
            response = self.api_handler.post(request, self.course_id)
            
            # Verify asyncio.run was called with create_sections
            mock_asyncio_run.assert_called_once()
            args, _ = mock_asyncio_run.call_args
            self.assertEqual(args[0].__name__, 'create_sections')
            
            # Verify response
            self.assertEqual(response.status_code, HTTPStatus.CREATED)
            self.assertEqual(len(response.data), len(self.section_names))
            
    def test_create_sections_validation_error(self):
        """Test that serializer validates section count doesn't exceed 60."""
        # Create request with too many sections
        request_data = {"sections": [f"Section {i}" for i in range(61)]}
        request = self.factory.post(
            f'/api/canvas/courses/{self.course_id}/sections',
            data=request_data,
            format='json'
        )
        request.data = request_data
        
        # Mock the error response
        mock_error_response = {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'message': "The list cannot be more than 60 items."
        }
        self.mock_canvas_error_handler.handle_serializer_errors.return_value = MagicMock(
            to_dict=MagicMock(return_value=mock_error_response)
        )
        
        # Execute the API call
        response = self.api_handler.post(request, self.course_id)
        
        # Verify response
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertIn("The list cannot be more than 60 items", str(response.data))