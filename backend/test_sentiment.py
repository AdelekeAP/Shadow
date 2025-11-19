"""
Test script for sentiment analysis
"""
from app.services.sentiment_analysis import analyze_sentiment

# Test cases
test_texts = [
    "I'm feeling really stressed about my exams coming up",
    "Great day! Finished all my assignments early",
    "Just working on my project, nothing special",
    "I can't handle this workload anymore, it's too much",
    "Feeling confident about the upcoming test!"
]

print("🧪 Testing Sentiment Analysis\n")
print("=" * 60)

for text in test_texts:
    result = analyze_sentiment(text)
    if result:
        print(f"\n📝 Text: {text}")
        print(f"   Score: {result['sentiment_score']} ({result['label']})")
        print(f"   Confidence: {result['confidence']*100:.1f}%")
    else:
        print(f"\n❌ Failed to analyze: {text}")

print("\n" + "=" * 60)
print("✅ Sentiment analysis test complete!")
