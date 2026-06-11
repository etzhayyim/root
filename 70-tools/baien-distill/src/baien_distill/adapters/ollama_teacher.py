"""OpenAI-compatible client for on-fleet teachers (Ollama / LiteLLM).

`openai` is imported lazily so this module can be imported (and the
LangGraph DAG built) in environments that don't have it — only the
teacher-generation path actually instantiates the client.
"""

from __future__ import annotations

import os


class OllamaTeacher:
    """Thin wrapper that targets an OpenAI-compatible endpoint on the LAN.

    Ollama exposes OpenAI-compat at /v1; LiteLLM (judah :4000) exposes a
    proper bearer-auth gateway. Both share the same interface here.
    """

    def __init__(self, *, base_url: str, model_id: str,
                 api_key: str | None = None) -> None:
        import openai  # lazy

        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key or os.environ.get("LITELLM_KEY") or "dummy",
        )
        self.model_id = model_id

    def complete(self, prompt: str, *, max_tokens: int = 512,
                 temperature: float = 0.7) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def health(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
