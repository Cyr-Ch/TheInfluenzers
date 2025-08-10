import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Import the module to test
from trend_result_formatter import (
    TrendResultFormatter,
    save_youtube_trending_videos,
    save_youtube_trending_topics,
    save_youtube_trending_music,
    save_tiktok_trending
)


class TestTrendResultFormatter(unittest.TestCase):
    """Test cases for TrendResultFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.formatter = TrendResultFormatter(output_dir=self.temp_dir)
        
        # Sample YouTube video data
        self.sample_video = {
            "id": "test_video_id_123",
            "title": "Test Video Title",
            "channelTitle": "Test Channel",
            "publishedAt": "2024-01-01T00:00:00Z",
            "viewCount": "1000",
            "likeCount": "100",
            "commentCount": "50",
            "categoryId": "22",
            "tags": ["test", "video", "trending"],
            "description": "A test video description that is not very long"
        }
        
        # Sample video with captions
        self.sample_video_with_captions = {
            **self.sample_video,
            "captions": {
                "language": "en",
                "is_auto": False,
                "format": "srt",
                "method": "manual",
                "content": "Sample caption content"
            }
        }
        
        # Sample video with long description
        self.sample_video_long_desc = {
            **self.sample_video,
            "description": "A" * 2500  # Very long description
        }
        
        # Sample TikTok data
        self.sample_tiktok_data = {
            "hashtags": [
                {"hashtag": "#test1", "count": 1000000},
                {"hashtag": "#test2", "count": 500000}
            ],
            "sounds": [
                {"sound_name": "Test Sound 1", "play_count": 2000000},
                {"sound_name": "Test Sound 2", "play_count": 1500000}
            ]
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test TrendResultFormatter initialization."""
        formatter = TrendResultFormatter("custom_output")
        self.assertEqual(formatter.output_dir, Path("custom_output"))
        
        # Test default output directory
        formatter_default = TrendResultFormatter()
        self.assertEqual(formatter_default.output_dir, Path("trend_results"))
    
    def test_format_youtube_videos_basic(self):
        """Test basic YouTube video formatting."""
        videos = [self.sample_video]
        result = self.formatter.format_youtube_videos(videos, "US", True)
        
        self.assertIn("videos", result)
        self.assertIn("metadata", result)
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["metadata"]["region_code"], "US")
        self.assertEqual(result["metadata"]["data_type"], "trending_videos")
        
        video = result["videos"][0]
        self.assertEqual(video["video_id"], "test_video_id_123")
        self.assertEqual(video["title"], "Test Video Title")
        self.assertEqual(video["channel"], "Test Channel")
        self.assertEqual(video["statistics"]["views"], 1000)
        self.assertEqual(video["statistics"]["likes"], 100)
        self.assertEqual(video["statistics"]["comments"], 50)
    
    def test_format_youtube_videos_with_captions(self):
        """Test YouTube video formatting with captions."""
        videos = [self.sample_video_with_captions]
        result = self.formatter.format_youtube_videos(videos, "US", True)
        
        video = result["videos"][0]
        self.assertTrue(video["captions"]["available"])
        self.assertEqual(video["captions"]["language"], "en")
        self.assertFalse(video["captions"]["is_auto_generated"])
        self.assertEqual(video["captions"]["format"], "srt")
        self.assertEqual(video["captions"]["method"], "manual")
    
    def test_format_youtube_videos_without_captions(self):
        """Test YouTube video formatting without captions."""
        videos = [self.sample_video]
        result = self.formatter.format_youtube_videos(videos, "US", True)
        
        video = result["videos"][0]
        self.assertFalse(video["captions"]["available"])
    
    def test_format_youtube_videos_long_description(self):
        """Test YouTube video formatting with long description truncation."""
        videos = [self.sample_video_long_desc]
        result = self.formatter.format_youtube_videos(videos, "US", True)
        
        video = result["videos"][0]
        self.assertEqual(len(video["description"]), 2003)  # 2000 + "..."
        self.assertTrue(video["description"].endswith("..."))
    
    def test_format_youtube_videos_missing_data(self):
        """Test YouTube video formatting with missing data."""
        incomplete_video = {
            "id": "test_id",
            "title": "Test Title"
            # Missing other fields
        }
        videos = [incomplete_video]
        result = self.formatter.format_youtube_videos(videos, "US", True)
        
        video = result["videos"][0]
        self.assertEqual(video["channel"], "")
        self.assertEqual(video["statistics"]["views"], 0)
        self.assertEqual(video["statistics"]["likes"], 0)
        self.assertEqual(video["statistics"]["comments"], 0)
        self.assertEqual(video["tags"], [])
    
    def test_format_youtube_topics(self):
        """Test YouTube topics formatting."""
        topics = ["Topic 1", "Topic 2", "Topic 3"]
        result = self.formatter.format_youtube_topics(topics, "US", True)
        
        self.assertIn("topics", result)
        self.assertEqual(result["total_count"], 3)
        self.assertEqual(result["metadata"]["data_type"], "trending_topics")
        
        for i, topic in enumerate(result["topics"]):
            self.assertEqual(topic["rank"], i + 1)
            self.assertEqual(topic["title"], f"Topic {i + 1}")
            self.assertEqual(topic["word_count"], 2)
    
    def test_format_youtube_music(self):
        """Test YouTube music formatting."""
        music_videos = [self.sample_video]
        result = self.formatter.format_youtube_music(music_videos, "US", True)
        
        self.assertIn("music_videos", result)
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["metadata"]["data_type"], "trending_music")
        self.assertEqual(result["metadata"]["category"], "Music (ID: 10)")
    
    def test_format_tiktok_trends(self):
        """Test TikTok trends formatting."""
        result = self.formatter.format_tiktok_trends(self.sample_tiktok_data, True)
        
        self.assertIn("hashtags", result)
        self.assertIn("sounds", result)
        self.assertEqual(result["hashtags"]["total_count"], 2)
        self.assertEqual(result["sounds"]["total_count"], 2)
        
        # Check hashtag formatting
        hashtag = result["hashtags"]["trending"][0]
        self.assertEqual(hashtag["rank"], 1)
        self.assertEqual(hashtag["hashtag"], "#test1")
        self.assertEqual(hashtag["play_count"], 1000000)
        self.assertEqual(hashtag["formatted_count"], "1.0M")
        
        # Check sound formatting
        sound = result["sounds"]["trending"][0]
        self.assertEqual(sound["rank"], 1)
        self.assertEqual(sound["sound_name"], "Test Sound 1")
        self.assertEqual(sound["play_count"], 2000000)
        self.assertEqual(sound["formatted_count"], "2.0M")
    
    def test_format_large_numbers(self):
        """Test large number formatting."""
        formatter = TrendResultFormatter()
        
        self.assertEqual(formatter._format_large_number(999), "999")
        self.assertEqual(formatter._format_large_number(1500), "1.5K")
        self.assertEqual(formatter._format_large_number(1500000), "1.5M")
        self.assertEqual(formatter._format_large_number(2500000000), "2.5B")
    
    def test_save_to_json(self):
        """Test JSON file saving."""
        test_data = {"test": "data", "number": 42}
        filename = "test_output.json"
        
        filepath = self.formatter.save_to_json(test_data, filename, True)
        
        # Check file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Check file contents
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
        
        # Test without .json extension
        filepath2 = self.formatter.save_to_json(test_data, "test_output2", False)
        self.assertTrue(filepath2.endswith('.json'))
    
    def test_save_to_json_pretty_print(self):
        """Test JSON file saving with and without pretty printing."""
        test_data = {"test": "data"}
        
        # With pretty print
        filepath_pretty = self.formatter.save_to_json(test_data, "pretty.json", True)
        with open(filepath_pretty, 'r', encoding='utf-8') as f:
            content_pretty = f.read()
        
        # Without pretty print
        filepath_compact = self.formatter.save_to_json(test_data, "compact.json", False)
        with open(filepath_compact, 'r', encoding='utf-8') as f:
            content_compact = f.read()
        
        # Pretty print should have more whitespace
        self.assertGreater(len(content_pretty), len(content_compact))
    
    @patch('trend_result_formatter.fetch_youtube_trending_videos')
    def test_format_and_save_youtube_videos(self, mock_fetch):
        """Test fetch, format, and save YouTube videos."""
        mock_fetch.return_value = [self.sample_video]
        
        filepath = self.formatter.format_and_save_youtube_videos(
            region_code="US",
            max_results=10,
            include_captions=False
        )
        
        mock_fetch.assert_called_once_with(
            region_code="US",
            max_results=10,
            include_captions=False,
            caption_language='en',
            api_key=None
        )
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('youtube_trending_videos_US_', filepath)
    
    @patch('trend_result_formatter.fetch_youtube_trending_topics')
    def test_format_and_save_youtube_topics(self, mock_fetch):
        """Test fetch, format, and save YouTube topics."""
        mock_fetch.return_value = ["Topic 1", "Topic 2"]
        
        filepath = self.formatter.format_and_save_youtube_topics(
            region_code="CA",
            max_results=15
        )
        
        mock_fetch.assert_called_once_with(
            region_code="CA",
            max_results=15,
            api_key=None
        )
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('youtube_trending_topics_CA_', filepath)
    
    @patch('trend_result_formatter.fetch_youtube_trending_music')
    def test_format_and_save_youtube_music(self, mock_fetch):
        """Test fetch, format, and save YouTube music."""
        mock_fetch.return_value = [self.sample_video]
        
        filepath = self.formatter.format_and_save_youtube_music(
            region_code="GB",
            max_results=20
        )
        
        mock_fetch.assert_called_once_with(
            region_code="GB",
            max_results=20,
            api_key=None
        )
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('youtube_trending_music_GB_', filepath)
    
    @patch('trend_result_formatter.get_tiktok_trending')
    def test_format_and_save_tiktok_trends(self, mock_fetch):
        """Test fetch, format, and save TikTok trends."""
        mock_fetch.return_value = self.sample_tiktok_data
        
        filepath = self.formatter.format_and_save_tiktok_trends()
        
        mock_fetch.assert_called_once_with(api_key=None)
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('tiktok_trending_', filepath)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('trend_result_formatter.fetch_youtube_trending_videos')
    def test_save_youtube_trending_videos(self, mock_fetch):
        """Test save_youtube_trending_videos convenience function."""
        mock_fetch.return_value = [{"id": "test", "title": "Test"}]
        
        filepath = save_youtube_trending_videos(
            region_code="US",
            max_results=5,
            output_dir=self.temp_dir
        )
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('youtube_trending_videos_US_', filepath)
    
    @patch('trend_result_formatter.fetch_youtube_trending_topics')
    def test_save_youtube_trending_topics(self, mock_fetch):
        """Test save_youtube_trending_topics convenience function."""
        mock_fetch.return_value = ["Topic 1"]
        
        filepath = save_youtube_trending_topics(
            region_code="CA",
            output_dir=self.temp_dir
        )
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('youtube_trending_topics_CA_', filepath)
    
    @patch('trend_result_formatter.fetch_youtube_trending_music')
    def test_save_youtube_trending_music(self, mock_fetch):
        """Test save_youtube_trending_music convenience function."""
        mock_fetch.return_value = [{"id": "test", "title": "Test"}]
        
        filepath = save_youtube_trending_music(
            region_code="GB",
            output_dir=self.temp_dir
        )
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('youtube_trending_music_GB_', filepath)
    
    @patch('trend_result_formatter.get_tiktok_trending')
    def test_save_tiktok_trending(self, mock_fetch):
        """Test save_tiktok_trending convenience function."""
        mock_fetch.return_value = {"hashtags": [], "sounds": []}
        
        filepath = save_tiktok_trending(output_dir=self.temp_dir)
        
        self.assertTrue(filepath.endswith('.json'))
        self.assertIn('tiktok_trending_', filepath)


if __name__ == '__main__':
    unittest.main()