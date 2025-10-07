# Updated test_llm.py to check for free tier
import openai
import os
from dotenv import load_dotenv

def check_openai_status():
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    print("🔍 Checking OpenAI Account Status...")
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Check usage
        usage = client.usage.retrieve()
        print(f"📊 Usage info: {usage}")
        
        # Test with very minimal call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print("✅ Account is active!")
        return True
        
    except openai.RateLimitError as e:
        print("❌ Rate limit exceeded - Check:")
        print("   • Billing at: https://platform.openai.com/account/billing")
        print("   • Usage limits")
        print("   • Free credits may be expired")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_openai_status()