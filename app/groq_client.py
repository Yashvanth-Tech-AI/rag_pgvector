"""Thin wrapper around the Groq Python SDK."""

import re
# pyrefly: ignore [missing-import]
from groq import Groq, AuthenticationError, GroqError


class GroqLLM:
    """Generate grounded answers using a Groq-hosted open model."""

    def __init__(self, api_key: str, model: str):
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send a system + user prompt to Groq and return the text answer."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw_text = response.choices[0].message.content or ""
            # Strip internal <think>...</think> reasoning tags if present
            cleaned_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
            return cleaned_text
        except AuthenticationError:
            return (
                "[ERROR] Groq API authentication failed.\n"
                "Please edit your `.env` file and update GROQ_API_KEY with your actual key from https://console.groq.com/keys"
            )
        except GroqError as e:
            return f"[ERROR] Groq API Error: {e}"

