"""
Test configuration and utilities for TheInfluenzers project tests.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch


class TestConfig:
    """Test configuration constants and utilities."""
    
    # Test data constants
    SAMPLE_VIDEO_ID = "test_video_id_123"
    SAMPLE_CHANNEL_TITLE = "Test Channel"
    SAMPLE_VIDEO_TITLE = "Test Video Title"
    SAMPLE_DESCRIPTION = "A test video description that is not very long"
    
    # Test API responses
    SAMPLE_YOUTUBE_VIDEO = {
        "id": SAMPLE_VIDEO_ID,
        "title": SAMPLE_VIDEO_TITLE,
        "channelTitle": SAMPLE_CHANNEL_TITLE,
        "publishedAt": "2024-01-01T00:00:00Z",
        "viewCount": "1000",
        "likeCount": "100",
        "commentCount": "50",
        "categoryId": "22",
        "tags": ["test", "video", "trending"],
        "description": SAMPLE_DESCRIPTION
    }
    
    SAMPLE_TIKTOK_DATA = {
        "hashtags": [
            {"hashtag": "#test1", "count": 1000000},
            {"hashtag": "#test2", "count": 500000},
            {"hashtag": "#trending", "count": 750000}
        ],
        "sounds": [
            {"sound_name": "Test Sound 1", "play_count": 2000000},
            {"sound_name": "Test Sound 2", "play_count": 1500000}
        ]
    }
    
    # Test file paths
    TEST_OUTPUT_DIR = "test_output"
    TEST_DATA_DIR = "test_data"


class TempDirManager:
    """Context manager for temporary directories."""
    
    def __init__(self, prefix="test_"):
        self.prefix = prefix
        self.temp_dir = None
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix=self.prefix)
        return self.temp_dir
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class MockAPIClient:
    """Mock API client for testing."""
    
    @staticmethod
    def mock_youtube_api_response():
        """Return a mock YouTube API response."""
        return {
            "items": [
                {
                    "id": "video_id_1",
                    "snippet": {
                        "title": "Test Video 1",
                        "channelTitle": "Test Channel 1",
                        "description": "Test description 1",
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "tags": ["test", "video"]
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "100",
                        "commentCount": "50"
                    }
                }
            ]
        }
    
    @staticmethod
    def mock_openai_response():
        """Return a mock OpenAI API response."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"analysis": "test analysis"}'
        return mock_response


def create_test_file(filepath, content=""):
    """Create a test file with given content."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def cleanup_test_files(*filepaths):
    """Clean up test files."""
    for filepath in filepaths:
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
        except (OSError, FileNotFoundError):
            pass


def mock_environment_variables(**env_vars):
    """Context manager to mock environment variables."""
    original_env = {}
    
    for key, value in env_vars.items():
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = value
    
    try:
        yield
    finally:
        # Restore original values
        for key in env_vars:
            if key in original_env:
                os.environ[key] = original_env[key]
            else:
                os.environ.pop(key, None)


def assert_file_exists(filepath):
    """Assert that a file exists."""
    assert os.path.exists(filepath), f"File {filepath} does not exist"


def assert_file_content(filepath, expected_content):
    """Assert file content matches expected content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        actual_content = f.read()
    
    assert actual_content == expected_content, \
        f"File content mismatch. Expected: {expected_content}, Got: {actual_content}"


def assert_json_file_structure(filepath, expected_keys):
    """Assert JSON file has expected structure."""
    import json
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for key in expected_keys:
        assert key in data, f"Key '{key}' not found in JSON file"


# Common test fixtures
@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with TempDirManager() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_youtube_video():
    """Provide a sample YouTube video for tests."""
    return TestConfig.SAMPLE_YOUTUBE_VIDEO.copy()


@pytest.fixture
def sample_tiktok_data():
    """Provide sample TikTok data for tests."""
    return TestConfig.SAMPLE_TIKTOK_DATA.copy()


@pytest.fixture
def mock_openai_client():
    """Provide a mock OpenAI client for tests."""
    with patch('openai.OpenAI') as mock_client:
        yield mock_client


# Import pytest if available for fixtures
try:
    import pytest
except ImportError:
    # pytest not available, skip fixtures
    pass