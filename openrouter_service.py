
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 🔹 Character limiter (FINAL)
def limit_text(text, max_chars=500):
    if len(text) <= max_chars:
        return text

    trimmed = text[:max_chars]

    # end at sentence if possible
    if "." in trimmed:
        return trimmed.rsplit(".", 1)[0] + "."
    else:
        return trimmed.rsplit(" ", 1)[0] + "..."

def generate_response(prompt: str) -> str:
    try:
        payload = {
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "system",
                    "content": "Answer clearly and completely in under 400 characters."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            # ❌ removed max_tokens completely
        }

        response = requests.post(URL, headers=headers, json=payload)

        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        return limit_text(reply, 500)  # 🔥 strict 400 char limit

    except Exception as e:
        return f"Error: {str(e)}"


def agri_expert_response(question: str) -> str:
    prompt = f"""
You are an agriculture expert helping Indian farmers.

Give:
- Crop suggestions
- Fertilizer advice
- Irrigation tips

Answer clearly and completely in under 400 characters.

Question: {question}
"""
    return generate_response(prompt)