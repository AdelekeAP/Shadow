"""
Test YouTube Integration
Verifies YouTube API key works and content curation functions properly
"""
import os
from dotenv import load_dotenv
from app.services.youtube_service import get_youtube_service
from app.services.content_curator import get_content_curator

load_dotenv()


def test_youtube_service():
    """Test basic YouTube service functionality"""
    print("\n" + "="*60)
    print("🎥 Testing YouTube Service")
    print("="*60 + "\n")

    youtube = get_youtube_service()

    if not youtube.youtube:
        print("❌ YouTube service not initialized - API key missing or invalid")
        return False

    print("✅ YouTube service initialized successfully\n")

    # Test 1: Search for videos
    print("📝 Test 1: Searching for Python tutorial videos...")
    try:
        videos = youtube.search_videos(
            query="Python data structures tutorial",
            max_results=3,
            duration="medium"
        )

        if videos:
            print(f"✅ Found {len(videos)} videos")
            for i, video in enumerate(videos, 1):
                print(f"\n   Video {i}:")
                print(f"   Title: {video['title'][:60]}...")
                print(f"   Channel: {video['channel_title']}")
                print(f"   Views: {video['view_count']:,}")
                print(f"   Likes: {video['like_count']:,}")
                print(f"   Like/View Ratio: {video['like_view_ratio']}%")
                print(f"   URL: {video['url']}")
        else:
            print("⚠️ No videos found")
            return False

    except Exception as e:
        print(f"❌ Error searching videos: {e}")
        return False

    # Test 2: Get video transcript
    print(f"\n📝 Test 2: Getting transcript for first video...")
    try:
        video_id = videos[0]['video_id']
        transcript = youtube.get_video_transcript(video_id)

        if transcript:
            print(f"✅ Retrieved transcript ({len(transcript)} characters)")
            print(f"   Preview: {transcript[:200]}...")
        else:
            print("⚠️ No transcript available for this video (this is normal)")

    except Exception as e:
        print(f"⚠️ Transcript retrieval error: {e} (this is normal for some videos)")

    # Test 3: Get curated videos (with quality scoring)
    print(f"\n📝 Test 3: Getting curated high-quality videos...")
    try:
        curated = youtube.get_curated_videos(
            topic="binary search algorithm",
            max_results=2,
            min_quality_score=50.0
        )

        if curated:
            print(f"✅ Found {len(curated)} curated videos")
            for i, video in enumerate(curated, 1):
                print(f"\n   Curated Video {i}:")
                print(f"   Title: {video['title'][:60]}...")
                print(f"   Quality Score: {video['quality_score']}/100")
                print(f"   Has Transcript: {video.get('has_transcript', False)}")
                if 'comment_sentiment' in video:
                    print(f"   Positive Comments: {video['comment_sentiment']['positive_percentage']}%")
        else:
            print("⚠️ No curated videos found")

    except Exception as e:
        print(f"❌ Error getting curated videos: {e}")
        return False

    print("\n" + "="*60)
    print("✅ YouTube Service Tests Passed!")
    print("="*60 + "\n")
    return True


def test_content_curator():
    """Test content curator with YouTube only"""
    print("\n" + "="*60)
    print("✨ Testing Content Curator (YouTube Only)")
    print("="*60 + "\n")

    curator = get_content_curator()

    print("📝 Curating resources for 'React hooks tutorial'...")
    try:
        results = curator.curate_resources(
            topic="React hooks tutorial",
            learning_style="visual",
            max_results=3,
            min_quality_score=60.0
        )

        print(f"\n✅ Curation Complete!")
        print(f"   Topic: {results['topic']}")
        print(f"   Learning Style: {results['learning_style']}")
        print(f"   YouTube Videos: {len(results['videos'])}")
        print(f"   Reddit Resources: {len(results['reddit_resources'])} (not configured)")
        print(f"   Combined Recommendations: {len(results['combined_recommendations'])}")

        if results['combined_recommendations']:
            print(f"\n   📊 Top Recommendation:")
            top = results['combined_recommendations'][0]
            print(f"   Title: {top['title'][:60]}...")
            print(f"   Type: {top['type']}")
            print(f"   Quality Score: {top['quality_score']}/100")
            print(f"   URL: {top['url']}")

        print("\n" + "="*60)
        print("✅ Content Curator Tests Passed!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"❌ Error in content curator: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting YouTube Integration Tests...\n")

    # Check API key
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in environment")
        print("   Please add it to your .env file")
        exit(1)

    print(f"✅ YouTube API Key found: {api_key[:10]}...{api_key[-10:]}\n")

    # Run tests
    youtube_ok = test_youtube_service()

    if youtube_ok:
        curator_ok = test_content_curator()

        if curator_ok:
            print("\n🎉 All tests passed! YouTube integration is working perfectly.\n")
        else:
            print("\n⚠️ Content curator tests failed. Check the errors above.\n")
    else:
        print("\n⚠️ YouTube service tests failed. Check the errors above.\n")
