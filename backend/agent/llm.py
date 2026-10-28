"""
Claude (Anthropic API) client shared by every LLM step.

Two helpers:
  complete(prompt)              -> plain text (drafts, appeals)
  complete_json(prompt, schema) -> dict guaranteed to match a JSON schema,
                                   using Claude structured outputs
                                   (output_config.format = json_schema)

Design notes for current Claude models (e.g. claude-sonnet-5-5):
  * temperature / top_p / top_k are NOT sent - these models reject them.
  * Effort is set per call (output_config.effort). Simple met/unmet checks
    use "low" to keep latency and cost down; drafting uses "medium".
  * Adaptive thinking may add `thinking` blocks; we read only `text` blocks.
  * Forced tool_choice is not supported, so JSON comes from structured
    outputs rather than a forced tool call.
  * EVERY failure (API errors, rate limits, refusals, truncation, bad JSON)
    is raised as LLMError, so callers handle one exception type.
  * A process-wide semaphore caps concurrent Claude calls (batch requests x
    parallel criteria) to stay within rate limits.

The client is created lazily so modules can be imported (e.g. in tests)
without an API key.
"""
import json
import os
import threading

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "8000"))
MAX_CONCURRENCY = int(os.getenv("ANTHROPIC_MAX_CONCURRENCY", "4"))
MAX_RETRIES = int(os.getenv("ANTHROPIC_MAX_RETRIES", "3"))

_client = None
_client_lock = threading.Lock()
_slots = threading.BoundedSemaphore(MAX_CONCURRENCY)


class LLMError(RuntimeError):
    """Raised when Claude returns no usable answer, for any reason."""


def get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                from anthropic import Anthropic  # reads ANTHROPIC_API_KEY
                _client = Anthropic(max_retries=MAX_RETRIES)  # SDK retries 429/5xx with backoff
    return _client


def _text_of(response) -> str:
    return "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ).strip()


def _check_stop(response) -> None:
    if response.stop_reason == "refusal":
        raise LLMError("Claude declined to answer this request")
    if response.stop_reason == "max_tokens":
        raise LLMError("Response was cut off; raise ANTHROPIC_MAX_TOKENS")


def _create(prompt: str, system: str | None, max_tokens: int, output_config: dict):
    kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        # Sent via extra_body so it works across SDK versions.
        "extra_body": {"output_config": output_config},
    }
    if system:
        kwargs["system"] = system
    try:
        with _slots:
            return get_client().messages.create(**kwargs)
    except LLMError:
        raise
    except Exception as exc:  # anthropic.APIError, network errors, missing key, ...
        name = type(exc).__name__
        status = getattr(exc, "status_code", None)
        raise LLMError(f"Claude API error ({name}{f' {status}' if status else ''})") from exc


def complete(prompt: str, system: str | None = None, max_tokens: int = MAX_TOKENS,
             effort: str = "medium") -> str:
    response = _create(prompt, system, max_tokens, {"effort": effort})
    _check_stop(response)
    return _text_of(response)


def complete_json(prompt: str, schema: dict, system: str | None = None,
                  max_tokens: int = MAX_TOKENS, effort: str = "low") -> dict:
    response = _create(prompt, system, max_tokens, {
        "effort": effort,
        "format": {"type": "json_schema", "schema": schema},
    })
    _check_stop(response)
    try:
        return json.loads(_text_of(response))
    except json.JSONDecodeError as exc:
        raise LLMError(f"Claude returned invalid JSON: {exc}") from exc
