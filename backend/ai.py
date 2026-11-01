"""Provider layer: Gemini, Groq, OpenRouter. Provider keys are stored per account.
When a key's quota is used up the next active key is tried; when none is left
AllKeysExhausted is raised so the UI can ask for a new key."""
import httpx

from . import db, secret_store

PROVIDERS = {
    "gemini": {"label": "Google Gemini", "default_model": "gemini-2.5-flash",
               "get_key": "https://aistudio.google.com/apikey"},
    "groq": {"label": "Groq", "default_model": "llama-3.3-70b-versatile",
             "get_key": "https://console.groq.com/keys"},
    "openrouter": {"label": "OpenRouter (free models)",
                   "default_model": "meta-llama/llama-3.3-70b-instruct:free",
                   "get_key": "https://openrouter.ai/keys"},
}
OPENAI_STYLE = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}


class ProviderError(Exception):
    def __init__(self, kind, msg):
        super().__init__(msg)
        self.kind = kind


class AllKeysExhausted(Exception):
    pass


class NoKey(Exception):
    pass


def _classify(status, text):
    t = text.lower()
    if status in (429, 402) or "quota" in t or "rate limit" in t or "resource_exhausted" in t:
        return "quota"
    if status in (401, 403) or "api key not valid" in t or "invalid api key" in t:
        return "invalid"
    return "other"


def call_provider(provider, model, key, messages, timeout=60):
    """messages: [{role: system|user|assistant, content: str}] -> reply text."""
    try:
        if provider == "gemini":
            system = "\n".join(m["content"] for m in messages if m["role"] == "system")
            contents = [{"role": "model" if m["role"] == "assistant" else "user",
                         "parts": [{"text": m["content"]}]}
                        for m in messages if m["role"] != "system"]
            body = {"contents": contents}
            if system:
                body["systemInstruction"] = {"parts": [{"text": system}]}
            r = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key}, json=body, timeout=timeout)
        elif provider in OPENAI_STYLE:
            r = httpx.post(
                OPENAI_STYLE[provider],
                headers={"Authorization": "Bearer " + key},
                json={"model": model, "messages": messages},
                timeout=timeout,
            )
        else:
            raise ProviderError("other", f"Unknown provider: {provider}")
    except httpx.HTTPError as e:
        raise ProviderError("other", f"Network error: {e}")
    if r.status_code != 200:
        raise ProviderError(_classify(r.status_code, r.text), r.text[:300])
    data = r.json()
    try:
        if provider == "gemini":
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ProviderError("other", "Unexpected response from provider.")


def complete(messages):
    """Try each active key in order; mark dead ones; raise when none works."""
    with db.conn() as c:
        keys = c.execute("SELECT * FROM api_keys ORDER BY id").fetchall()
    if not keys:
        raise NoKey()
    for k in keys:
        if k["status"] != "active":
            continue
        try:
            key = secret_store.decrypt_api_key(k["api_key"])
            return call_provider(k["provider"], k["model"], key, messages)
        except ProviderError as e:
            if e.kind in ("quota", "invalid"):
                new = "exhausted" if e.kind == "quota" else "invalid"
                with db.conn() as c:
                    c.execute("UPDATE api_keys SET status=? WHERE id=?", (new, k["id"]))
                continue
            raise
    raise AllKeysExhausted()
