"""Small Groq transport; credentials and raw provider error bodies never escape."""

import json
import os
import urllib.error
import urllib.request
import time
from contextlib import contextmanager
from contextvars import ContextVar

_deadline = ContextVar("company_provider_deadline", default=None)


@contextmanager
def time_budget(seconds):
    token = _deadline.set(time.monotonic() + max(0, seconds))
    try:
        yield
    finally:
        _deadline.reset(token)


def remaining_timeout(default):
    end = _deadline.get()
    remaining = min(default, end - time.monotonic()) if end is not None else default
    if remaining < 0.1:
        raise ProviderUnavailable("budget")
    return remaining


class ProviderUnavailable(Exception):
    def __init__(self, provider, code=None):
        self.provider = provider
        self.code = code
        super().__init__("Investigator provider is unavailable")


def groq_completion(messages, tools, first=False, final=False, schema=None):
    body = dict(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        messages=messages,
        tools=[dict(type="function", function=t) for t in tools],
        tool_choice="none" if final else "required" if first else "auto",
        temperature=0.1,
        max_completion_tokens=1400,
        parallel_tool_calls=False,
    )
    if body["model"].startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"
    if final:
        body.pop("tools", None)
        body.pop("tool_choice", None)
        body.pop("parallel_tool_calls", None)
        body["response_format"] = (
            {
                "type": "json_schema",
                "json_schema": {
                    "name": "company_investigation",
                    "strict": True,
                    "schema": schema,
                },
            }
            if schema and body["model"].startswith("openai/gpt-oss")
            else {"type": "json_object"}
        )
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + os.environ["GROQ_API_KEY"],
            "Content-Type": "application/json",
            "User-Agent": "ChronosGraph-reference-demo",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=remaining_timeout(25)) as response:
            parsed = json.load(response)
        return parsed["choices"][0]["message"]
    except urllib.error.HTTPError as error:
        failure = ProviderUnavailable("groq", error.code)
        try:
            payload = json.loads(error.read())
            code = payload.get("error", {}).get("code")
            failure.category = (
                code
                if code
                in {
                    "tool_use_failed",
                    "rate_limit_exceeded",
                    "model_not_found",
                    "invalid_api_key",
                    "model_decommissioned",
                }
                else "provider_request_rejected"
            )
        except (ValueError, OSError):
            failure.category = "provider_request_rejected"
        failure.rate_limits = {
            key: error.headers.get(key)
            for key in [
                "x-ratelimit-limit-tokens",
                "x-ratelimit-remaining-tokens",
                "x-ratelimit-remaining-requests",
                "retry-after",
            ]
        }
        raise failure from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ProviderUnavailable("groq") from None


def openrouter_completion(messages, tools, first=False, final=False, schema=None):
    """Free-model router only. No automatic paid-model fallback is permitted."""
    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    if model != "openrouter/free" and not model.endswith(":free"):
        raise ValueError("OpenRouter is restricted to free models")
    body = dict(
        model=model,
        messages=messages,
        temperature=0.1,
        max_tokens=1800,
        provider={"require_parameters": True},
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "company_investigation",
                "strict": True,
                "schema": schema,
            },
        }
        if schema
        else {"type": "json_object"},
    )
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
            "X-Title": "ChronosGraph",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=remaining_timeout(35)) as response:
            parsed = json.load(response)
        message = parsed["choices"][0]["message"]
        message["_model"] = str(parsed.get("model", model))[:160]
        return message
    except urllib.error.HTTPError as error:
        # Provider body can contain prompts or secrets. Never propagate or log it.
        raise ProviderUnavailable("openrouter", error.code) from None
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError):
        raise ProviderUnavailable("openrouter") from None
