"""Cohere API runner — same interface as HFModelRunner.

Uses Cohere's OpenAI-compatible endpoint (https://docs.cohere.com/docs/compatibility-api)
so it can reuse the `openai` client, mirroring the pattern in sarvam.py.
"""

import os
import time
from openai import OpenAI


class CohereRunner:
    def __init__(self, model_name: str, device: str = None):
        self.model_name = model_name.split("/")[-1]
        self.client = OpenAI(
            base_url="https://api.cohere.ai/compatibility/v1",
            api_key=os.environ.get("COHERE_API_KEY", ""),
        )

    def _call(self, prompt: str, max_new_tokens: int, temperature: float) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer concisely and directly without explanation or reasoning.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max(256, max_new_tokens),
            temperature=temperature,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def generate(self, prompt: str, max_new_tokens: int = 128, temperature: float = 0.2) -> str:
        result = self._call(prompt, max_new_tokens, temperature)
        if not result:
            print("[WARN] Cohere returned empty output, retrying after 10s...")
            time.sleep(10)
            result = self._call(prompt, max_new_tokens, temperature)
        if not result:
            print("[WARN] Cohere returned empty output on retry, skipping.")
        return result
