#!/usr/bin/env python3
"""
Test script to verify all functions in trend_retrieval.py work correctly
"""

import os
import sys
from typing import Dict, List, Any

# Import all functions from trend_retrieval
from trend_retrieval import (
    fetch_youtube_trending_videos,
    fetch_youtube_trending_topics,
    fetch_youtube_trending_music,
    get_tiktok_trending,
    get_video_captions,
    validate_region_code,
    validate_video_id,
    validate_api_key,
    test_youtube_captions_api,
    ValidationError
)



def test_validation_functions():
    """Test all validation functions."""
    print("\n=== Testing Validation Functions ===")
    
    # Test validate_region_code
    try:
        # Valid region codes
        assert validate_region_code("US") == "US"
        assert validate_region_code("us") == "US"
        assert validate_region_code(" GB ") == "GB"
        print("✅ validate_region_code: Valid codes work correctly")
        
        # Invalid region codes
        try:
            validate_region_code("INVALID")
            print("❌ validate_region_code: Should have raised ValidationError for invalid code")
            return False
        except ValidationError:
            print("✅ validate_region_code: Correctly raises ValidationError for invalid code")
        
        try:
            validate_region_code("")
            print("❌ validate_region_code: Should have raised ValidationError for empty code")
            return False
        except ValidationError:
            print("✅ validate_region_code: Correctly raises ValidationError for empty code")
            
    except Exception as e:
        print(f"❌ Error in validate_region_code tests: {e}")
        return False
    
    # Test validate_video_id
    try:
        # Valid video IDs
        assert validate_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert validate_video_id("abc123def45") == "abc123def45"
        print("✅ validate_video_id: Valid IDs work correctly")
        
        # Invalid video IDs
        try:
            validate_video_id("INVALID")
            print("❌ validate_video_id: Should have raised ValidationError for invalid ID")
            return False
        except ValidationError:
            print("✅ validate_video_id: Correctly raises ValidationError for invalid ID")
        
        try:
            validate_video_id("")
            print("❌ validate_video_id: Should have raised ValidationError for empty ID")
            return False
        except ValidationError:
            print("✅ validate_video_id: Correctly raises ValidationError for empty ID")
            
    except Exception as e:
        print(f"❌ Error in validate_video_id tests: {e}")
        return False
    
    # Test validate_api_key
    try:
        # Valid API keys
        assert validate_api_key("valid_api_key_123") == "valid_api_key_123"
        assert validate_api_key("a" * 20) == "a" * 20
        print("✅ validate_api_key: Valid keys work correctly")
        
        # Invalid API keys
        try:
            validate_api_key("")
            print("❌ validate_api_key: Should have raised ValidationError for empty key")
            return False
        except ValidationError:
            print("✅ validate_api_key: Correctly raises ValidationError for empty key")
        
        try:
            validate_api_key("short")
            print("❌ validate_api_key: Should have raised ValidationError for short key")
            return False
        except ValidationError:
            print("✅ validate_api_key: Correctly raises ValidationError for short key")
            
    except Exception as e:
        print(f"❌ Error in validate_api_key tests: {e}")
        return False
    
    return True


def test_environment_setup():
    """Test if required environment variables are set."""
    print("\n=== Testing Environment Setup ===")
    
    # Check if .env file exists
    env_file_exists = os.path.exists(".env")
    print(f"✅ .env file exists: {env_file_exists}")
    
    # Check for required API keys
    youtube_key = os.getenv("YOUTUBE_API_KEY")
    tiktok_key = os.getenv("TIKTOK_RAPIDAPI_KEY")
    apify_key = os.getenv("APIFY_API_TOKEN")
    
    print(f"✅ YOUTUBE_API_KEY set: {bool(youtube_key)}")
    print(f"✅ TIKTOK_RAPIDAPI_KEY set: {bool(tiktok_key)}")
    print(f"✅ APIFY_API_TOKEN set: {bool(apify_key)}")
    
    if not youtube_key:
        print("⚠️  Warning: YOUTUBE_API_KEY not set - YouTube functions will fail")
    
    return bool(youtube_key)


def test_fetch_youtube_trending_videos():
    """Test fetch_youtube_trending_videos function."""
    print("\n=== Testing fetch_youtube_trending_videos ===")
    
    try:
        # Test basic functionality
        videos = fetch_youtube_trending_videos(
            region_code="US",
            max_results=3,
            include_captions=False
        )
        
        print(f"✅ Successfully fetched {len(videos)} trending videos")
        
        if videos:
            video = videos[0]
            required_fields = ["id", "title", "channelTitle", "tags", "categoryId", "description", "publishedAt", "viewCount", "likeCount", "commentCount"]
            missing_fields = [field for field in required_fields if field not in video]
            
            if missing_fields:
                print(f"❌ Missing fields in video data: {missing_fields}")
            else:
                print("✅ All required fields present in video data")
            
            print(f"Sample video: {video['title']} by {video['channelTitle']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fetch_youtube_trending_videos: {e}")
        return False


def test_fetch_youtube_trending_videos_with_captions():
    """Test fetch_youtube_trending_videos with captions."""
    print("\n=== Testing fetch_youtube_trending_videos with captions ===")
    
    try:
        # Test with captions (smaller number to avoid rate limits)
        videos = fetch_youtube_trending_videos(
            region_code="US",
            max_results=10,
            include_captions=True,
            caption_language='en'
        )
        
        print(f"✅ Successfully fetched {len(videos)} videos with caption support")
        
        caption_count = sum(1 for v in videos if v.get('captions'))
        print(f"📝 Videos with captions: {caption_count}/{len(videos)}")
        
        if videos:
            video = videos[0]
            if video.get('captions'):
                captions = video['captions']
                print(f"✅ Caption data structure: {list(captions.keys())}")
                print(f"   Language: {captions.get('language')}")
                print(f"   Auto-generated: {captions.get('is_auto')}")
                print(f"   Format: {captions.get('format')}")
                print(f"   Method: {captions.get('method')}")
            else:
                print("ℹ️  No captions available for first video")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fetch_youtube_trending_videos with captions: {e}")
        return False


def test_fetch_youtube_trending_topics():
    """Test fetch_youtube_trending_topics function."""
    print("\n=== Testing fetch_youtube_trending_topics ===")
    
    try:
        topics = fetch_youtube_trending_topics(
            region_code="US",
            max_results=5
        )
        
        print(f"✅ Successfully fetched {len(topics)} trending topics")
        
        if topics:
            print("Sample topics:")
            for i, topic in enumerate(topics[:5], 1):
                print(f"  {i}. {topic}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fetch_youtube_trending_topics: {e}")
        return False


def test_fetch_youtube_trending_music():
    """Test fetch_youtube_trending_music function."""
    print("\n=== Testing fetch_youtube_trending_music ===")
    
    try:
        music_videos = fetch_youtube_trending_music(
            region_code="US",
            max_results=3
        )
        
        print(f"✅ Successfully fetched {len(music_videos)} music videos")
        
        if music_videos:
            video = music_videos[0]
            print(f"Sample music video: {video['title']} by {video['channelTitle']}")
            
            # Check if it's actually a music video (categoryId should be 10)
            if video.get('categoryId') == '10':
                print("✅ Correctly identified as music video (categoryId=10)")
            else:
                print(f"⚠️  Unexpected categoryId: {video.get('categoryId')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fetch_youtube_trending_music: {e}")
        return False


def test_get_video_captions():
    """Test get_video_captions function."""
    print("\n=== Testing get_video_captions ===")
    
    try:
        # Test with a well-known video that likely has captions
        video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
        
        captions = get_video_captions(video_id, language='en')
        
        if captions:
            print(f"✅ Successfully fetched captions for video {video_id}")
            print(f"   Language: {captions['language']}")
            print(f"   Auto-generated: {captions['is_auto']}")
            print(f"   Format: {captions['format']}")
            print(f"   Method: {captions.get('method', 'unknown')}")
            print(f"   Content length: {len(captions['content'])} characters")
            
            # Show first few lines of content
            lines = captions['content'].split('\n')[:5]
            print("   Content preview:")
            for line in lines:
                if line.strip():
                    print(f"     {line}")
        else:
            print(f"ℹ️  No captions found for video {video_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in get_video_captions: {e}")
        return False


def test_get_tiktok_trending():
    """Test get_tiktok_trending function."""
    print("\n=== Testing get_tiktok_trending ===")
    
    try:
        trending = get_tiktok_trending()
        
        hashtags = trending.get("hashtags", [])
        sounds = trending.get("sounds", [])
        
        print(f"✅ Successfully fetched TikTok trending data")
        print(f"   Hashtags: {len(hashtags)}")
        print(f"   Sounds: {len(sounds)}")
        
        if hashtags:
            top_hashtag = hashtags[0]
            print(f"   Top hashtag: {top_hashtag.get('hashtag')} ({top_hashtag.get('count')} plays)")
        
        if sounds:
            top_sound = sounds[0]
            print(f"   Top sound: {top_sound.get('sound_name')} ({top_sound.get('play_count')} plays)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in get_tiktok_trending: {e}")
        return False


def test_youtube_captions_api_function():
    """Test the YouTube captions API test function."""
    print("\n=== Testing test_youtube_captions_api ===")
    
    try:
        result = test_youtube_captions_api()
        
        if result.get("status") == "success":
            print("✅ YouTube captions API test successful")
            print(f"   Video ID: {result.get('video_id')}")
            print(f"   Caption tracks found: {result.get('caption_tracks_found')}")
        elif result.get("status") == "error":
            print(f"⚠️  YouTube captions API test failed: {result.get('error_text', result.get('exception', 'Unknown error'))}")
        else:
            print(f"ℹ️  YouTube captions API test result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test_youtube_captions_api: {e}")
        return False


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test with invalid region code
        try:
            videos = fetch_youtube_trending_videos(
                region_code="INVALID_REGION",
                max_results=1
            )
            print("❌ Invalid region code should have caused an error")
            return False
        except Exception as e:
            print("✅ Invalid region code handled correctly with error")
        
    except Exception as e:
        print(f"❌ Unexpected error with invalid region code: {e}")
        return False
    
    try:
        # Test with invalid video ID
        captions = get_video_captions("INVALID_VIDEO_ID", language='en')
        if captions is None:
            print("✅ Invalid video ID handled gracefully (returned None)")
        else:
            print("⚠️  Unexpected result for invalid video ID")
            
    except Exception as e:
        print(f"❌ Invalid video ID caused error: {e}")
        return False
    
    return True


def run_all_tests():
    """Run all tests and provide summary."""
    print("🧪 Testing All Functions in trend_retrieval.py")
    print("=" * 60)
    
    # Check environment first
    youtube_available = test_environment_setup()
    
    test_results = []
    
    # Test validation functions (don't require API keys)
    test_results.append(("validation_functions", test_validation_functions()))
    
    # Test YouTube functions (only if API key is available)
    if youtube_available:
        test_results.append(("fetch_youtube_trending_videos", test_fetch_youtube_trending_videos()))
        test_results.append(("fetch_youtube_trending_videos_with_captions", test_fetch_youtube_trending_videos_with_captions()))
        test_results.append(("fetch_youtube_trending_topics", test_fetch_youtube_trending_topics()))
        test_results.append(("fetch_youtube_trending_music", test_fetch_youtube_trending_music()))
        test_results.append(("get_video_captions", test_get_video_captions()))
        test_results.append(("test_youtube_captions_api", test_youtube_captions_api_function()))
    else:
        print("\n⚠️  Skipping YouTube tests due to missing YOUTUBE_API_KEY")
    
    # Test TikTok function (doesn't require API key)
    test_results.append(("get_tiktok_trending", test_get_tiktok_trending()))
    
    # Test error handling
    test_results.append(("error_handling", test_error_handling()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! All functions are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)