"""AirLLM provider for layer-sharded inference on constrained GPU hardware."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from agent33.llm.base import ChatMessage, LLMResponse

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Optional airllm import - only available when GPU extras installed
try:
    from airllm import AutoModel as AirLLMAutoModel
except ImportError:
    AirLLMAutoModel = None  # type: ignore[assignment,misc]

try:
    from transformers import AutoTokenizer
except ImportError:
    AutoTokenizer = None  # type: ignore[assignment,misc]


def _format_chat(messages: list[ChatMessage], tokenizer: object | None = None) -> str:
    """Format chat messages into a prompt string.

    Uses the tokenizer's chat template if available, otherwise falls back
    to a simple role-prefixed format.
    """
    if tokenizer is not None and hasattr(tokenizer, "apply_chat_template"):
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]
        try:
            return tokenizer.apply_chat_template(  # type: ignore[union-attr]
                msg_dicts, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            logger.debug("chat template failed, falling back to simple format")

    parts: list[str] = []
    for m in messages:
        parts.append(f"<|{m.role}|>\n{m.content}")
    parts.append("<|assistant|>")
    return "\n".join(parts)


class AirLLMProvider:
    """Layer-sharded LLM inference via airllm.

    Loads one transformer layer at a time onto the GPU, enabling 70B+
    model inference on hardware with as little as 4 GB VRAM.
    """

    def __init__(
        self,
        model_path: str,
        device: str = "cuda:0",
        compression: str = "",
        max_seq_len: int = 2048,
        prefetch: bool = True,
    ) -> None:
        if AirLLMAutoModel is None:
            raise ImportError(
                "airllm is not installed. Install with: pip install airllm"
            )
        self._model_path = model_path
        self._device = device
        self._compression = compression
        self._max_seq_len = max_seq_len
        self._prefetch = prefetch
        self._model: object | None = None
        self._tokenizer: object | None = None
        self._lock = asyncio.Lock()

    async def _ensure_loaded(self) -> None:
        """Lazy-load model and tokenizer on first use (thread-safe)."""
        if self._model is not None:
            return
        async with self._lock:
            if self._model is not None:
                return
            logger.info(
                "loading airllm model from %s (compression=%s, prefetch=%s)",
                self._model_path,
                self._compression or "none",
                self._prefetch,
            )
            loop = asyncio.get_running_loop()
            self._model, self._tokenizer = await loop.run_in_executor(
                None, self._load_sync
            )
            logger.info("airllm model loaded successfully")

    def _load_sync(self) -> tuple[object, object]:
        """Synchronous model loading (runs in executor)."""
        kwargs: dict[str, object] = {
            "device": self._device,
            "prefetching": self._prefetch,
        }
        if self._compression == "4bit":
            kwargs["compression"] = "4bit"
        elif self._compression == "8bit":
            kwargs["compression"] = "8bit"

        model = AirLLMAutoModel.from_pretrained(  # type: ignore[union-attr]
            self._model_path, **kwargs
        )
        tokenizer = AutoTokenizer.from_pretrained(self._model_path)  # type: ignore[union-attr]
        return model, tokenizer

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion using layer-sharded inference."""
        await self._ensure_loaded()

        prompt = _format_chat(messages, self._tokenizer)
        gen_tokens = max_tokens or 512

        loop = asyncio.get_running_loop()
        output_text, prompt_len = await loop.run_in_executor(
            None, self._generate_sync, prompt, gen_tokens, temperature
        )

        return LLMResponse(
            content=output_text,
            model=f"airllm-{self._model_path.split('/')[-1]}",
            prompt_tokens=prompt_len,
            completion_tokens=len(output_text.split()),
        )

    def _generate_sync(
        self, prompt: str, max_new_tokens: int, temperature: float
    ) -> tuple[str, int]:
        """Synchronous generation (runs in executor)."""
        import torch  # type: ignore[import-untyped]

        tokenizer = self._tokenizer
        input_ids = tokenizer(  # type: ignore[misc]
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self._max_seq_len,
        ).input_ids

        prompt_len = input_ids.shape[1]

        generation_output = self._model.generate(  # type: ignore[union-attr]
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            return_dict_in_generate=True,
            temperature=temperature,
        )

        output_ids = generation_output.sequences[0][prompt_len:]
        text: str = tokenizer.decode(output_ids, skip_special_tokens=True)  # type: ignore[union-attr]
        return text, prompt_len

    async def list_models(self) -> list[str]:
        """Return the single model this provider serves."""
        name = self._model_path.split("/")[-1] if "/" in self._model_path else self._model_path
        return [f"airllm-{name}"]
