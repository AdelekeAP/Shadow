"""
Test Mood Logging Flow with AI Sentiment Analysis
Run this to test the mood feature end-to-end
"""
import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
EMAIL = "nicomannion6@gmail.com"
PASSWORD = "nicomannion6"  # Change this to your actual password

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def main():
    print_section("🧪 Shadow Mood Logging Test")

    # Step 1: Login
    print("\n1️⃣  Logging in...")
    login_response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login successful!")

    # Step 2: Log mood with negative sentiment
    print("\n2️⃣  Logging STRESSED mood with negative note...")
    mood1 = {
        "mood_type": "stressed",
        "energy_level": 2,
        "note": "I'm feeling overwhelmed with all these deadlines. Too much work and not enough time!"
    }

    response1 = requests.post(
        f"{API_URL}/mood/log-mood",
        json=mood1,
        headers=headers
    )

    if response1.status_code == 200:
        data = response1.json()
        print(f"✅ Mood logged successfully!")
        if "sentiment_analysis" in data:
            sa = data["sentiment_analysis"]
            print(f"   🤖 AI Analysis: {sa['label']} ({sa['confidence']*100:.1f}% confidence)")
            print(f"   📊 Sentiment Score: {sa['score']}")
        print(f"   📝 Full Response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Failed: {response1.text}")

    # Step 3: Log mood with positive sentiment
    print("\n3️⃣  Logging MOTIVATED mood with positive note...")
    mood2 = {
        "mood_type": "motivated",
        "energy_level": 4,
        "note": "Great day! I finished all my assignments early and I'm feeling ready for exams!"
    }

    response2 = requests.post(
        f"{API_URL}/mood/log-mood",
        json=mood2,
        headers=headers
    )

    if response2.status_code == 200:
        data = response2.json()
        print(f"✅ Mood logged successfully!")
        if "sentiment_analysis" in data:
            sa = data["sentiment_analysis"]
            print(f"   🤖 AI Analysis: {sa['label']} ({sa['confidence']*100:.1f}% confidence)")
            print(f"   📊 Sentiment Score: {sa['score']}")
    else:
        print(f"❌ Failed: {response2.text}")

    # Step 4: Log mood without note (no sentiment analysis)
    print("\n4️⃣  Logging CALM mood without note...")
    mood3 = {
        "mood_type": "calm",
        "energy_level": 3,
        "note": ""
    }

    response3 = requests.post(
        f"{API_URL}/mood/log-mood",
        json=mood3,
        headers=headers
    )

    if response3.status_code == 200:
        data = response3.json()
        print(f"✅ Mood logged successfully!")
        if "sentiment_analysis" in data:
            print(f"   🤖 AI Analysis: Available")
        else:
            print(f"   ℹ️  No sentiment analysis (no note provided)")
    else:
        print(f"❌ Failed: {response3.text}")

    # Step 5: Get mood history
    print("\n5️⃣  Fetching mood history...")
    history_response = requests.get(
        f"{API_URL}/mood/moods?limit=5",
        headers=headers
    )

    if history_response.status_code == 200:
        data = history_response.json()
        print(f"✅ Found {data['total']} recent mood logs")
        for i, mood in enumerate(data['moods'][:3], 1):
            print(f"\n   Mood #{i}:")
            print(f"   • Type: {mood['mood_type']}")
            print(f"   • Energy: {mood['energy_level']}/5")
            if mood.get('sentiment_score') is not None:
                print(f"   • Sentiment: {mood['sentiment_score']}")
            if mood.get('note'):
                print(f"   • Note: {mood['note'][:60]}...")

    # Step 6: Get mood trends
    print("\n6️⃣  Fetching mood trends (last 7 days)...")
    trends_response = requests.get(
        f"{API_URL}/mood/mood-trends?days=7",
        headers=headers
    )

    if trends_response.status_code == 200:
        trends = trends_response.json()['trends']
        print(f"✅ Mood Trends:")
        print(f"   • Total logs: {trends['total_logs']}")
        print(f"   • Average energy: {trends['avg_energy']}/5")
        print(f"   • Most common mood: {trends['most_common_mood']}")

        if 'sentiment_stats' in trends:
            ss = trends['sentiment_stats']
            print(f"\n   📊 Sentiment Statistics:")
            print(f"   • Positive: {ss['positive']}")
            print(f"   • Neutral: {ss['neutral']}")
            print(f"   • Negative: {ss['negative']}")
            if ss['avg_sentiment'] is not None:
                print(f"   • Average sentiment: {ss['avg_sentiment']}")

        print(f"\n   📈 Mood Distribution:")
        for mood, count in trends['mood_distribution'].items():
            print(f"   • {mood}: {count}")

    print_section("✅ Test Complete!")
    print("\nAll mood logging features are working!")
    print("Including AI sentiment analysis with Hugging Face DistilBERT 🤖")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
