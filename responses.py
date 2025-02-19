import httpx
from random import choice

DATABASE_SERVICE_URL = "http://localhost:8000/respond"

async def get_response(user_input: str) -> str:
    """
    Given user_input, query the chat responses API to find a matching response.
    If no matching response is found or an error occurs, return a default fallback message.
    """
    # If the input is empty, return a specific message
    if not user_input.strip():
        return "Well you're awfully silent."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                DATABASE_SERVICE_URL,
                params={"input_text": user_input.lower()}
            )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", fallback_response())
        else:
            return fallback_response()
    
    except Exception as e:
        print(f"Exception occurred: {e}")
        return fallback_response()

def fallback_response() -> str:
    """Return one of the default fallback responses."""
    return choice([
        "I don't know what you mean by that.",
        "I don't understand.",
        "I'm sorry, I don't know what you mean."
    ])