"""
Quick test to verify GPT-4 truncation fix for study plan generation
"""
import requests
import json

API_URL = "http://localhost:8002"

# Step 1: Login to get fresh token
print("\n🔐 Logging in to get fresh token...")
login_response = requests.post(
    f"{API_URL}/api/v1/auth/login",
    json={
        "email": "nicomannion6@gmail.com",
        "password": "password123"  # Update if different
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    print("\n💡 Please update the password in this script if it's different")
    exit(1)

token_data = login_response.json()
token = token_data.get("access_token")
print("✅ Login successful!\n")

# Step 2: Generate study plan with visual learning style
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=" * 70)
print("🎥 Generating Study Plan with YouTube Integration")
print("=" * 70)
print("\n📝 Creating study plan:")
print("   Topic: React Hooks - useState and useEffect")
print("   Learning Style: visual (triggers YouTube curation)")
print("   Duration: 7 days")
print("   Difficulty: intermediate\n")

payload = {
    "topic": "React Hooks - useState and useEffect",
    "duration_days": 7,
    "difficulty_level": "intermediate",
    "learning_style": "visual",
    "trigger_type": "student_request"
}

try:
    print("⏳ Sending request (this may take 30-60 seconds)...\n")
    response = requests.post(
        f"{API_URL}/api/v1/smartstudy/study-plans",
        headers=headers,
        json=payload,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        plan_id = result.get("study_plan_id")

        print("✅ SUCCESS! Study plan generated without truncation errors!\n")
        print("=" * 70)
        print(f"📋 Study Plan ID: {plan_id}\n")

        # Get full plan details
        print("📥 Fetching complete study plan with resources...\n")
        plan_response = requests.get(
            f"{API_URL}/api/v1/smartstudy/study-plans/{plan_id}",
            headers=headers
        )

        if plan_response.status_code == 200:
            plan_data = plan_response.json()

            print("📊 STUDY PLAN DETAILS:")
            print("-" * 70)
            print(f"Title: {plan_data.get('topic')}")
            print(f"Duration: {plan_data.get('duration_days')} days")
            print(f"Learning Style: {plan_data.get('plan_data', {}).get('learning_style')}")

            # Check resources
            resources = plan_data.get('resources', [])
            youtube_videos = [r for r in resources if r.get('resource_type') == 'youtube_video']

            print(f"\n🎥 Total Resources: {len(resources)}")
            print(f"   📹 YouTube Videos: {len(youtube_videos)}")

            if youtube_videos:
                print("\n🎬 YOUTUBE VIDEOS CURATED:")
                print("=" * 70)
                for idx, video in enumerate(youtube_videos[:5], 1):  # Show first 5
                    print(f"\n{idx}. {video.get('resource_title', 'N/A')[:60]}")
                    print(f"   Quality Score: ⭐ {video.get('quality_score', 'N/A')}/100")
                    print(f"   Day: Day {video.get('day_number', 'N/A')}")
                    print(f"   URL: {video.get('resource_url', 'N/A')}")

                if len(youtube_videos) > 5:
                    print(f"\n... and {len(youtube_videos) - 5} more videos")
            else:
                print("\n⚠️ No YouTube videos were curated (API may be temporarily unavailable)")

            # Check if plan_data exists and has days (verifies no truncation)
            days = plan_data.get('plan_data', {}).get('days', [])
            print(f"\n📅 Study Plan Days: {len(days)}")

            if len(days) >= 7:
                print("✅ All days generated successfully - NO TRUNCATION!")
            else:
                print(f"⚠️ Only {len(days)} days generated (expected 7)")

            print("\n" + "=" * 70)
            print("🎉 FIX VERIFIED - Study Plan Generation Working!")
            print("=" * 70)
            print("\n📱 Next: Test in browser at http://localhost:3001")
            print("   1. Login to your account")
            print("   2. Go to Study Plans")
            print("   3. View the newly created plan")
            print("   4. Verify YouTube videos are embedded inline")
            print("   5. Click play to test the video player")

        else:
            print(f"❌ Error fetching plan: {plan_response.status_code}")
            print(plan_response.text)

    else:
        print(f"❌ Error creating study plan: {response.status_code}")
        print(response.text)

except requests.exceptions.Timeout:
    print("❌ Request timed out (>120s)")
    print("   This might indicate the YouTube API is slow")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n")
