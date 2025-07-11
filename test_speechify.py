import os
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()

SPEECHIFY_API_KEY = os.getenv('SPEECHIFY_API_KEY', '').strip()

async def test_speechify_api():
    """Test Speechify API endpoints"""
    print(f"Testing with API key: {SPEECHIFY_API_KEY[:10]}...")
    
    headers = {
        'Authorization': f'Bearer {SPEECHIFY_API_KEY}'
    }
    
    # Test different endpoints
    endpoints = [
        'https://api.sws.speechify.com/v1/voices',
        'https://api.sws.speechify.com/v1/audio/speech',
        'https://api.speechify.com/v1/voices',
        'https://api.speechify.com/v1/audio/speech'
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"\nTesting endpoint: {endpoint}")
            try:
                async with session.get(endpoint, headers=headers) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response: {data}")
                    else:
                        error_text = await response.text()
                        print(f"Error: {error_text}")
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_speechify_api()) 