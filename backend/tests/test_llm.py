"""Claude gateway tests (review findings #2 and #8). Uses a fake HTTP transport."""
import json

import anthropic
import pytest

import agent.llm as llm

try:  # newer SDKs ship their own httpx fork
    import httpx2 as httpx
except ImportError:  # pragma: no cover
    import httpx


def _client(handler):
    return anthropic.Anthropic(api_key="test", max_retries=0,
                               http_client=httpx.Client(transport=httpx.MockTransport(handler)))


def _ok(text, captured=None):
    def handler(request):
        if captured is not None:
            captured.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "msg", "type": "message", "role": "assistant", "model": llm.MODEL,
            "content": [{"type": "thinking", "thinking": "...", "signature": "s"},
                        {"type": "text", "text": text}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1}})
    return handler


def test_json_call_sends_schema_and_low_effort(monkeypatch):
    sent = []
    monkeypatch.setattr(llm, "_client", _client(_ok('{"status":"met","justification":"ok"}', sent)))
    out = llm.complete_json("p", {"type": "object"}, system="s")
    assert out == {"status": "met", "justification": "ok"}
    body = sent[0]
    assert body["output_config"]["effort"] == "low"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in body


def test_text_call_reads_only_text_blocks(monkeypatch):
    sent = []
    monkeypatch.setattr(llm, "_client", _client(_ok("hello", sent)))
    assert llm.complete("p") == "hello"
    assert sent[0]["output_config"] == {"effort": "medium"}


@pytest.mark.parametrize("status,err", [(429, "rate_limit_error"), (529, "overloaded_error"),
                                        (401, "authentication_error")])
def test_api_errors_become_llm_error(monkeypatch, status, err):
    monkeypatch.setattr(llm, "_client", _client(
        lambda r: httpx.Response(status, json={"type": "error", "error": {"type": err, "message": "x"}})))
    with pytest.raises(llm.LLMError, match=str(status)):
        llm.complete_json("p", {"type": "object"})


def test_refusal_becomes_llm_error(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={
            "id": "m", "type": "message", "role": "assistant", "model": llm.MODEL,
            "content": [{"type": "text", "text": "no"}], "stop_reason": "refusal",
            "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}})
    monkeypatch.setattr(llm, "_client", _client(handler))
    with pytest.raises(llm.LLMError, match="declined"):
        llm.complete("p")
