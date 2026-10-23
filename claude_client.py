"""Thin wrapper around the Claude API (Anthropic Python SDK)."""

import json

import anthropic

import prompts

DEFAULT_MODEL = "claude-opus-5-5"
MODEL_OPTIONS = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
# If a safety check declines a request, the API retries it on a fallback model.
# Haiku has no server-side fallback, so the option is only sent for these two.
FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}


class GiftGeniusError(Exception):
    """An error with a message that is safe to show in the UI."""


def _generate_json(api_key: str, model: str, system: str, user_input: str, schema: dict, effort: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    request = {
        "model": model,
        "max_tokens": 16000,
        "system": system,
        "messages": [{"role": "user", "content": user_input}],
        # Template pattern, enforced by the API: output must match this JSON schema.
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    }
    if model in FALLBACK_MODELS:
        request["betas"] = ["server-side-fallback-2026-07-01"]
        request["fallbacks"] = "default"

    try:
        response = client.beta.messages.create(**request)
    except anthropic.AuthenticationError as e:
        raise GiftGeniusError("Claude rejected the API key. Check ANTHROPIC_API_KEY in .streamlit/secrets.toml.") from e
    except anthropic.PermissionDeniedError as e:
        raise GiftGeniusError("This API key isn't allowed to use that model. Try another model in the sidebar.") from e
    except anthropic.NotFoundError as e:
        raise GiftGeniusError("That model isn't available for your key. Try another model in the sidebar.") from e
    except anthropic.RateLimitError as e:
        raise GiftGeniusError("Hit the API rate limit. Wait a minute and try again.") from e
    except anthropic.BadRequestError as e:
        if "credit balance" in str(e).lower():
            raise GiftGeniusError("Your Claude API credit balance is too low. Add credits at platform.claude.com.") from e
        raise GiftGeniusError(f"Claude rejected the request: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise GiftGeniusError(f"Claude's servers had a problem ({e.status_code}). Try again in a moment.") from e
    except anthropic.APIConnectionError as e:
        raise GiftGeniusError("Couldn't reach the Claude API. Check your internet connection.") from e

    if response.stop_reason == "refusal":
        raise GiftGeniusError("Claude declined this request. Try rewording the description.")
    if response.stop_reason == "max_tokens":
        raise GiftGeniusError("Claude's answer got cut off. Try again.")
    # Take the last text block: if a fallback model took over, its answer comes last.
    text = next((b.text for b in reversed(response.content) if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise GiftGeniusError("Claude returned something that wasn't valid JSON. Try again.") from e


def ask_questions(api_key: str, model: str, profile: str) -> list[dict]:
    data = _generate_json(api_key, model, prompts.DETECTIVE_SYSTEM, prompts.detective_input(profile), prompts.DETECTIVE_SCHEMA, effort="low")
    return data.get("questions", [])[:3]


def find_gifts(api_key: str, model: str, profile: str) -> dict:
    # Low effort halves the wait (about 12s vs 28s on Opus) with similar-quality ideas.
    data = _generate_json(api_key, model, prompts.GIFT_SYSTEM, prompts.gift_input(profile), prompts.GIFT_SCHEMA, effort="low")
    data["gifts"] = data.get("gifts", [])[:5]
    return data
