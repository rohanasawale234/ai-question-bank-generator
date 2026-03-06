from google import genai

client = genai.Client(api_key="AIzaSyBR5yzt46-WLwkcGgqg4qE0w2epKcWAGyE")

try:
    # Use Flash-Lite: it often has the most generous "No-Card" quota
    response = client.models.generate_content(
        model="gemini-1.5-flash-lite", 
        contents="Check if API is working"
    )
    print(f"✅ Success! Use 'gemini-1.5-flash-lite' in your project.")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")