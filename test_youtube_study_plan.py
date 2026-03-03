"""
Test YouTube Integration with Study Plans
Generates a study plan with visual learning style to test YouTube video curation
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Backend URL
API_URL = "http://localhost:8002"

# Get token from environment or use the one from your test file
TOKEN = os.getenv("TEST_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJuaWNvbWFubmlvbjZAZ21haWwuY29tIiwidXNlcl9pZCI6IjU5MTI2YjFjLWZmYWYtNDBjYi1iMzQ0LTY5NjFjOGY1ZTk5ZSIsImV4cCI6MTc2NDM4NDMzOX0.c-eBVUFql2_UmHYYqSTQWsRaJMXqnRd86op9aYUHUlY")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_generate_visual_study_plan():
    """Generate a study plan with visual learning style to trigger YouTube curation"""
    print("\n" + "="*70)
    print("🎥 Testing YouTube Integration with Study Plans")
    print("="*70 + "\n")

    print("📝 Generating study plan with VISUAL learning style...")
    print("   Topic: React Hooks")
    print("   Learning Style: visual (should trigger YouTube video curation)")
    print("   Duration: 7 days\n")

    payload = {
        "topic": "React Hooks - useState and useEffect",
        "duration_days": 7,
        "difficulty_level": "intermediate",
        "learning_style": "visual",  # This should trigger YouTube video curation
        "trigger_type": "student_request"
    }

    try:
        response = requests.post(
            f"{API_URL}/api/v1/smartstudy/study-plans",
            headers=headers,
            json=payload,
            timeout=60  # YouTube curation may take longer
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Study plan generated successfully!\n")

            plan_id = result.get("study_plan_id")
            print(f"📋 Study Plan ID: {plan_id}\n")

            # Get the full study plan details
            print("📥 Fetching study plan details with resources...\n")
            plan_response = requests.get(
                f"{API_URL}/api/v1/smartstudy/study-plans/{plan_id}",
                headers=headers
            )

            if plan_response.status_code == 200:
                plan_data = plan_response.json()

                print("=" * 70)
                print("📊 STUDY PLAN SUMMARY")
                print("=" * 70)
                print(f"Title: {plan_data.get('topic', 'N/A')}")
                print(f"Duration: {plan_data.get('duration_days', 'N/A')} days")
                print(f"Learning Style: {plan_data.get('plan_data', {}).get('learning_style', 'N/A')}")

                # Check for resources
                resources = plan_data.get('resources', [])
                print(f"\n🎥 Total Resources: {len(resources)}")

                if resources:
                    youtube_videos = [r for r in resources if r.get('resource_type') == 'youtube_video']
                    reddit_posts = [r for r in resources if r.get('resource_type') == 'reddit_post']

                    print(f"   📹 YouTube Videos: {len(youtube_videos)}")
                    print(f"   💬 Reddit Posts: {len(reddit_posts)}")

                    if youtube_videos:
                        print("\n" + "=" * 70)
                        print("🎬 CURATED YOUTUBE VIDEOS")
                        print("=" * 70)

                        for idx, video in enumerate(youtube_videos, 1):
                            print(f"\nVideo {idx}:")
                            print(f"  Title: {video.get('resource_title', 'N/A')[:70]}...")
                            print(f"  Quality Score: ⭐ {video.get('quality_score', 'N/A')}/100")
                            print(f"  Day: Day {video.get('day_number', 'N/A')}")
                            print(f"  URL: {video.get('resource_url', 'N/A')}")
                            if video.get('resource_description'):
                                print(f"  Description: {video.get('resource_description', '')[:100]}...")
                    else:
                        print("\n⚠️ No YouTube videos were curated. This could mean:")
                        print("   1. YouTube API key is not configured")
                        print("   2. Content curation service is not enabled")
                        print("   3. No videos found for this topic")
                else:
                    print("\n⚠️ No resources were attached to this study plan.")
                    print("   YouTube integration may not be active yet.")

                # Show day breakdown
                days = plan_data.get('plan_data', {}).get('days', [])
                if days:
                    print("\n" + "=" * 70)
                    print("📅 DAY-BY-DAY BREAKDOWN")
                    print("=" * 70)

                    for day in days[:3]:  # Show first 3 days
                        day_num = day.get('day_number', 'N/A')
                        day_resources = [r for r in resources if r.get('day_number') == day_num]

                        print(f"\nDay {day_num}: {day.get('title', 'N/A')}")
                        print(f"  Focus: {day.get('focus', 'N/A')}")
                        print(f"  Activities: {len(day.get('activities', []))}")
                        print(f"  Resources: {len(day_resources)} (including {len([r for r in day_resources if r.get('resource_type') == 'youtube_video'])} videos)")

                    if len(days) > 3:
                        print(f"\n... and {len(days) - 3} more days")

                print("\n" + "=" * 70)
                print("✅ TEST COMPLETE!")
                print("=" * 70)
                print("\n📱 Next Steps:")
                print("   1. Open http://localhost:3001 in your browser")
                print("   2. Login to your account")
                print("   3. Navigate to Study Plans")
                print("   4. View the newly created plan")
                print("   5. Click 'Watch Video' to test YouTube player integration")
                print("\n" + "=" * 70)

            else:
                print(f"❌ Error fetching plan details: {plan_response.status_code}")
                print(plan_response.text)

        else:
            print(f"❌ Error generating study plan: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("❌ Request timed out. YouTube curation may be taking too long.")
        print("   The study plan may still be created. Check the database.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting YouTube + Study Plan Integration Test\n")

    # Check if backend is running
    try:
        health = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        if health.status_code == 200:
            print("✅ Backend is running\n")
        else:
            print("⚠️ Backend health check returned unexpected status\n")
    except:
        print("❌ Backend is not running. Please start it first:")
        print("   cd backend && source venv/bin/activate && uvicorn app.main:app --reload\n")
        exit(1)

    # Run the test
    test_generate_visual_study_plan()
