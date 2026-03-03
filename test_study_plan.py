"""
Quick test script for study plan generation
Run this to test if the API works before building the full UI
"""
import requests
import json

# NOTE: Replace this with a valid token from your browser
# 1. Login to Shadow at http://localhost:3001
# 2. Open browser DevTools (F12)
# 3. Go to Application > Local Storage > http://localhost:3001
# 4. Copy the value of "token"
TOKEN = "YOUR_TOKEN_HERE"

BASE_URL = "http://localhost:8000"

def test_generate_study_plan():
    """Test generating a study plan"""
    print("🧪 Testing Study Plan Generation...")
    print("-" * 60)

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    # Test data
    plan_request = {
        "topic": "Binary Search Trees",
        "duration_days": 7,
        "trigger_type": "student_request"
    }

    print(f"\n📤 Sending request:")
    print(json.dumps(plan_request, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/smartstudy/study-plans",
            headers=headers,
            json=plan_request,
            timeout=60  # GPT-4 can take a while
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS! Study plan generated!\n")
            print(f"Study Plan ID: {data.get('study_plan_id')}")
            print(f"Topic: {data.get('topic')}")
            print(f"Duration: {data.get('duration_days')} days")
            print(f"Tokens Used: {data.get('tokens_used')}")

            # Print plan structure
            plan_data = data.get('plan_data', {})
            print(f"\n📚 Plan Title: {plan_data.get('title')}")
            print(f"Description: {plan_data.get('description')}")
            print(f"Total Days: {len(plan_data.get('days', []))}")

            # Print first day as sample
            if plan_data.get('days'):
                day1 = plan_data['days'][0]
                print(f"\n📅 Day 1 Sample:")
                print(f"  Title: {day1.get('title')}")
                print(f"  Focus: {day1.get('focus')}")
                print(f"  Activities: {len(day1.get('activities', []))}")

                if day1.get('activities'):
                    activity1 = day1['activities'][0]
                    print(f"\n  🎯 First Activity:")
                    print(f"    Title: {activity1.get('title')}")
                    print(f"    Type: {activity1.get('activity_type')}")
                    print(f"    Time: {activity1.get('estimated_minutes')} mins")

            print("\n" + "=" * 60)
            print("✅ STUDY PLAN GENERATION WORKS!")
            print("=" * 60)

        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)

    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out (GPT-4 is slow, this is normal)")
        print("Try increasing timeout or check backend logs")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_get_study_plans():
    """Test getting all study plans"""
    print("\n\n🧪 Testing Get Study Plans...")
    print("-" * 60)

    headers = {
        "Authorization": f"Bearer {TOKEN}",
    }

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/smartstudy/study-plans",
            headers=headers,
            params={"active_only": False}
        )

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            plans = response.json()
            print(f"\n✅ Found {len(plans)} study plan(s)")

            for i, plan in enumerate(plans):
                print(f"\n  Plan {i+1}:")
                print(f"    ID: {plan.get('id')}")
                print(f"    Topic: {plan.get('topic')}")
                print(f"    Progress: {plan.get('completion_percentage')}%")
                print(f"    Active: {plan.get('is_active')}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("  SMARTSTUDY STUDY PLAN API TEST")
    print("=" * 60)

    if TOKEN == "YOUR_TOKEN_HERE":
        print("\n⚠️ ERROR: Please set your auth token first!")
        print("\nHow to get your token:")
        print("1. Login to Shadow at http://localhost:3001")
        print("2. Open browser DevTools (F12)")
        print("3. Go to: Application > Local Storage > http://localhost:3001")
        print("4. Copy the value of 'token'")
        print("5. Replace YOUR_TOKEN_HERE with your actual token")
        print("\nThen run: python test_study_plan.py")
    else:
        test_generate_study_plan()
        test_get_study_plans()
