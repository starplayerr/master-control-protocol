"""LLM client abstraction supporting Anthropic and OpenAI."""

from __future__ import annotations

from . import config


class LLMClient:
    """Unified interface for calling Anthropic or OpenAI models."""

    def __init__(
        self,
        provider: str = config.DEFAULT_PROVIDER,
        model: str | None = None,
        max_output_tokens: int = config.DEFAULT_MAX_OUTPUT_TOKENS,
    ):
        self.provider = provider
        self.model = model or config.DEFAULT_MODEL.get(provider, "")
        self.max_output_tokens = max_output_tokens
        self._client = self._init_client()

    def _init_client(self):
        if self.provider == "anthropic":
            import anthropic

            return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        elif self.provider == "openai":
            import openai

            return openai.OpenAI(api_key=config.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def generate(self, system_prompt: str, user_content: str) -> str:
        """Send a prompt to the LLM and return the text response."""
        if self.provider == "anthropic":
            return self._call_anthropic(system_prompt, user_content)
        else:
            return self._call_openai(system_prompt, user_content)

    def _call_anthropic(self, system_prompt: str, user_content: str) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_output_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return message.content[0].text

    def _call_openai(self, system_prompt: str, user_content: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_output_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content
