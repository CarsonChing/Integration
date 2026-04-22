# Agent integration: security and ethical guardrails

This project adds lightweight guardrails around a callable agent turn (validation, rate limiting, ethical screening, then a model call). The reference workflow lives in [`demo.py`](demo.py); reusable logic is in [`security.py`](security.py).

---

## 1. System overview

**Problem.** An LLM endpoint can be abused (high request volume, oversized prompts), fed malformed or noisy text, or prompted in ways that conflict with basic safety or policy expectations. Responses can also echo disallowed content. Without guardrails, those issues hit the model first, which increases cost, risk, and support burden.

**Workflow.** Each user turn should be checked **before** and **after** model execution:

1. **Rate limit** — per session (or user id), enforce a cap in a sliding time window.  
2. **Validate and sanitize** — type, emptiness, max length, and light cleanup of the prompt.  
3. **Ethical screen (input)** — block known high-risk request patterns.  
4. **Model** — call the real or stub model with the **sanitized** string.  
5. **Ethical screen (output)** — same policy checks on the model string before returning it.

**Key components.**

| Component | Role |
|-----------|------|
| [`InputValidator`](security.py) | `validate(input)` returns `(ok, cleaned_text)` or `(False, error_message)`; `sanitize(text)` normalizes text. |
| [`RateLimiter`](security.py) | `check(session_key)` returns `(ok, message)`; tracks timestamps per key. |
| [`EthicalGuard`](security.py) | `screen(text, context=...)` returns `(ok, message)`; logs warnings when content is flagged. |
| [`run_secured_agent_turn`](demo.py) | Orchestrates the five steps above and returns a small result dict with `stage` on failure. |

---

## 2. Threat model

The design assumes an **untrusted client** (or compromised session) talking to your agent over a network or UI. Relevant threats include:

- **Abuse / availability** — flooding the service with requests or huge payloads.  
- **Prompt integrity** — odd control characters, NUL bytes, markup noise, or extreme length that complicates parsing or inflates tokens.  
- **Policy and safety expectations** — requests that ask the model to ignore rules, bypass safety, or describe clearly harmful acts (demo patterns only; not a complete policy engine).  
- **Output risk** — model text that matches the same policy patterns before it is shown to the user.  
- **Non-goals for this repo** — this code does **not** provide authentication, transport TLS configuration for your whole stack, secrets rotation, or a full content-classification model.

---

## 3. Security measures implemented

### 3.1 Input validation and sanitization (`InputValidator`)

**Threats addressed:** oversized prompts, non-string input, empty noise, NUL and C0 control characters, mild HTML-like tag noise, runaway whitespace.

**How it works.** `validate` requires a `str`, runs `sanitize`, rejects empty results, then enforces `max_length` (default 1000). `sanitize` strips NUL, removes most control characters (keeps newline, tab, carriage return), trims, collapses horizontal whitespace, caps long newline runs, and removes simple `<...>` tags via a length-bounded regex. On failure, callers get a **short, user-facing** string (for example, length or type errors).

### 3.2 Rate limiting (`RateLimiter`)

**Threats addressed:** brute-force or accidental **request flooding** per session.

**How it works.** For each key (for example `session_id`), the limiter stores request timestamps, drops entries outside a sliding window (`window_seconds`, default 60), and rejects when the count would exceed `max_requests` (default 10). The window **slides** with time: old timestamps expire automatically, so limits reset without a separate “reset” clock.

### 3.3 Ethical guardrails (`EthicalGuard`)

**Threats addressed:** a narrow class of **inappropriate or explicitly harmful request patterns** (instruction hijacks, demo harm phrases). Also catches the same patterns in **model output** when used after the model step.

**How it works.** Patterns are compiled case-insensitively from literals or from a caller-supplied list. `screen` scans the full text; on a match it logs a **WARNING** with `context` (for example `user_input` vs `model_output`) and a **truncated excerpt** (about 120 characters), then returns a **generic policy message** to the user instead of echoing the blocked phrase.

### 3.4 Integration (`demo.py`)

**Threats addressed:** ensures the above steps run in a **fixed order** on every turn; optional DeepSeek call uses **HTTPS** with a CA bundle via **certifi** to reduce common TLS verification failures.

**How it works.** `run_secured_agent_turn(session_id, user_message)` returns `{"ok": True, "response": ...}` or `{"ok": False, "error": ..., "stage": ...}` where `stage` is one of `rate_limit`, `validation`, `ethics_input`, `ethics_output`. API keys are loaded with **python-dotenv** from `.env` into the environment.

---

## 4. How to use the security module

**Dependencies.** Install what [`demo.py`](demo.py) uses for `.env` loading and HTTPS CA verification:

```bash
pip install python-dotenv certifi
```

**Environment.** Create a `.env` file if you use DeepSeek (optional):

```text
DEEPSEEK_API_KEY=your_key_here
```

For an interactive session after the scripted demo, set `DEMO_CHAT=1` in the environment (see [`demo.py`](demo.py)).

**Use the classes directly** in your own orchestration:

```python
from security import InputValidator, RateLimiter, EthicalGuard

validator = InputValidator(max_length=2000)
limiter = RateLimiter(max_requests=20, window_seconds=60)
guard = EthicalGuard()  # or EthicalGuard(patterns=["your", "phrases"])

ok, msg = limiter.check("user-123")
if not ok:
    ...

ok, text_or_err = validator.validate(user_text)
if not ok:
    ...
sanitized = text_or_err

ok, msg = guard.screen(sanitized, context="user_input")
if not ok:
    ...
```

**Use the bundled workflow** for a full turn:

```python
import demo

result = demo.run_secured_agent_turn("session-id", "Hello")
```

**Tests.**

```bash
python3 -m unittest test_security -v
```

---

## 5. Limitations and future improvements

| Area | Limitation | Possible improvement |
|------|------------|----------------------|
| Rate limiting | In-memory only; not shared across processes or hosts. | Redis, API gateway, or service-mesh rate limits. |
| Ethical filter | Keyword / substring style; easy to paraphrase or obfuscate. | Hosted moderation APIs, classifiers, or allow/deny lists maintained by policy owners. |
| Sanitization | Not a full HTML or script sanitizer. | Use a dedicated HTML sanitizer if rendering user HTML; treat model output as untrusted when rendering. |
| Logging | Excerpts can still contain sensitive or identifying text. | Redaction pipelines, structured logging, retention limits, access control on logs. |
| AuthN / AuthZ | Not implemented. | Sessions, OAuth, mTLS, or API keys at the edge in addition to these checks. |
| Model errors | Network or API failures surface as a string in the response path. | Retries, circuit breakers, and user-safe error taxonomy. |

This README documents the **intent and behavior** of the assignment code. It is not a formal penetration test or compliance certification.
