# AI agent security measures and ethical guardrails
_Exported on 4/22/2026 at 23:10:46 GMT+8 from Cursor (3.1.15)_

---

**User**

Objective
Implement security measures and ethical guardrails for an AI agent system.
Learning Outcomes
By completing this assignment, you will: - Implement input validation and
sanitization - Add rate limiting to prevent abuse - Create ethical content filters -
Document security considerations
Requirements
0. Integration Scope (Required)
Integrate your security components into a callable workflow (script or app
backend) so they are exercised before/after model execution.
You do not need a full Streamlit UI for this assignment.
1. Input Validation (30%)
Implement input validation that: - Checks input length limits - Validates input
format - Sanitizes potentially harmful content - Returns helpful error messages
2. Rate Limiting (30%)
Implement rate limiting that: - Tracks request counts per user/session - Enforces
limits (e.g., 10 requests per minute) - Returns appropriate error when limit
exceeded - Resets after time window
3. Ethical Guardrails (30%)
Implement content filtering that: - Checks for harmful content patterns - Filters
inappropriate requests - Logs flagged content for review - Provides appropriate
user feedback
4. Documentation (10%)
Document your security measures: - What threats are addressed - How each
measure works - Limitations and future improvements

Deliverables
1. security.py - Security implementations (~100-150 lines):
• InputValidator class
• RateLimiter class
• EthicalGuard class
2. demo.py - Demonstration of security features
3. test_security.py - Basic tests for your security measures

Example Structure
class InputValidator:
def __init__(self, max_length=1000):
self.max_length = max_length
def validate(self, input_text: str) -> tuple[bool, str]:
if len(input_text) > self.max_length:
return False, f"Input exceeds {self.max_length} characters"
return True, "Valid"

---

**Cursor**

Exploring the workspace to see what's present and how we can integrate security into a callable workflow.



Workspace is nearly empty (only `.env` and `.gitignore`), so we're planning a greenfield Python implementation.



Confirming a greenfield project: we'll plan files, APIs, workflow integration, and documentation.



---

**User**

security.md and requirements.txt is not required

---

**Cursor**

Updating the plan to drop `SECURITY.md` and `requirements.txt`, and to place documentation elsewhere (e.g. stdlib tests).



Updating the plan: we'll satisfy the documentation requirement with a module docstring in `security.py` (and a short workflow note in `demo.py` if needed), and use the stdlib `unittest` suite so `requirements.txt` isn't needed.



Here is what changed in the plan:

**Removed**
- [`SECURITY.md`](SECURITY.md) and [`requirements.txt`](requirements.txt) from scope and from the file checklist.

**Documentation (10%)**
- Same rubric content, but delivered as a **module docstring at the top of [`security.py`](security.py)** (threats, how each measure works, limitations / future work). No extra markdown file.

**Tests**
- [`test_security.py`](test_security.py) will use **`unittest`** and **`unittest.mock`** (e.g. `patch` for time, **`assertLogs`** for flagged-content logging). Run with `python -m unittest test_security` — no third-party deps.

The plan file is updated: [`agent_security_guardrails_57d5e2a0.plan.md`](/Users/carsonching/.cursor/plans/agent_security_guardrails_57d5e2a0.plan.md). When you want this built in the repo, say to **execute the plan** (or similar) and we can implement it.

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

Implementing the plan: starting with `security.py`, then `demo.py` and `test_security.py`.



Collapsing internal whitespace in `sanitize` so NUL removal doesn't leave double spaces.



Here is what was implemented.

### [`security.py`](security.py) (134 lines)
- **`InputValidator`**: `validate()` returns `(True, sanitized_text)` or `(False, error)`; rejects non-`str`, empty-after-strip, and over `max_length`. **`sanitize()`** strips NUL, outer whitespace, collapses runs of spaces/tabs, trims long newline runs, removes simple `<...>` tags.
- **`RateLimiter`**: sliding window per key; **`check()`** returns an error when `max_requests` is already reached in `window_seconds` (11th call fails with 10/min defaults).
- **`EthicalGuard`**: configurable substring patterns (defaults are generic demo phrases); **`screen()`** logs a **WARNING** with `context` and a short **excerpt** when blocked.
- **Module docstring** covers threats, behavior, workflow order, and limitations (per plan, no `SECURITY.md`).

### [`demo.py`](demo.py)
- **`run_secured_agent_turn(session_id, user_message)`** runs: rate limit → validate (using returned sanitized text) → ethics on input → **`stub_model`** → ethics on output; returns `{"ok", "response"}` or `{"ok", "error", "stage"}`.
- **`__main__`** prints valid, over-long, rate-limited, and flagged examples.

### [`test_security.py`](test_security.py)
- **`unittest`** + **`patch("security.time.time", ...)`** for the rate limit window and **`assertLogs("security", level="WARNING")`** for flagged ethical content; includes two **`demo`** workflow checks.

Run tests from the assignment folder:

```bash
python3 -m unittest test_security -v
```

Run the demo:

```bash
python3 demo.py
```

All planned todos are **completed**; the old **SECURITY.md** todo stays **cancelled** as you requested earlier.

---

**User**

reduce notations, and check these criteria fultilled:
Input Validation & Sanitization - Robust validation rules, sanitization, clear user-facing errors
Rate Limiting & Abuse Control - Correct request tracking, limit enforcement, reset behavior
Ethical Guardrails  - Effective filtering and policy checks with appropriate user feedback
Integration Demonstration & Reliability - Security components are integrated into callable workflow and demonstrated clearly
If you need a collable workflow, can build a ultra-simple chatbot with deepseek api in .env

---

**Cursor**

Reviewing the implementation and trimming notation while verifying criteria; we'll add an optional Deepseek path only if `.env` supports it.



Compressing docstrings and type noise, hardening sanitization (strip disallowed control characters), and adding an optional secured Deepseek path via `.env` + stdlib `urllib` (no new dependencies).



Here is what changed and how it maps to your criteria.

### Notation trimmed
- **`security.py`**: Shorter module docstring (plain text, no markdown headings). Dropped `from __future__ import annotations`, generic `Pattern` typing, and per-method type hints.
- **`test_security.py`**: Removed `-> None` / other return annotations and the `# type: ignore` on `validate(None)` (still valid at runtime).
- **`demo.py`**: Minimal docstrings; workflow is obvious from code.

### Criteria check

| Criterion | How it is met |
|-----------|----------------|
| **Input validation & sanitization** | Type check, empty-after-clean, max length; **sanitize** removes NUL, **C0 control chars** (keeps `\n\t\r`), collapses spaces, long newline runs, simple `<...>` tags; errors are short and user-facing (`Input must be a string`, `cannot be empty`, `exceeds N characters`). |
| **Rate limiting & abuse control** | Per-session key, **sliding window** of timestamps, **reject when count ≥ limit** before recording the new hit, message states max and window; **reset** when old timestamps fall outside the window (tested with patched time). |
| **Ethical guardrails** | Case-insensitive substring patterns, **block** with a fixed policy message, **WARNING** log with `context` + short excerpt. |
| **Integration & reliability** | **`run_secured_agent_turn`** still runs rate → validate → ethics → model → ethics. **`deepseek_model`**: reads **`DEEPSEEK_API_KEY`** from the environment or **`.env`** (simple parser, no extra packages); if missing or on HTTP/JSON errors, falls back to **`stub_model`** or **`[model error] ...`**. **`python demo.py`** runs the four printed scenarios; **`python demo.py chat`** is a minimal secured REPL. |

### Deepseek / `.env`
Add a line (no quotes needed unless the value has spaces):

`DEEPSEEK_API_KEY=sk-...`

Uses `https://api.deepseek.com/chat/completions` (per DeepSeek docs). Tests pin **`model_fn=demo.stub_model`** so CI stays offline and deterministic.

### Commands
```bash
python3 -m unittest test_security -v
python3 demo.py              # scenarios; stub if no key
python3 demo.py chat         # secured stdin loop; uses API if key set
```

---

**User**

do not involve arguments, also use python-dotenv instead

---

**Cursor**

Reading `demo.py` and updating it to use `python-dotenv`, remove CLI arguments, and adjust tests if needed.



Switching to `python-dotenv`, removing `sys.argv` handling, and adding `requirements.txt`.



Removing the `model_fn` parameter from `run_secured_agent_turn` so the public API has no optional arguments.



Here is what changed:

### `python-dotenv`
- [`demo.py`](demo.py) uses `from dotenv import load_dotenv` and **`load_dotenv()`** at import time so **`DEEPSEEK_API_KEY`** comes from `.env` or the environment.
- Removed the hand-written `_read_dotenv` helper.
- Added [`requirements.txt`](requirements.txt) with `python-dotenv>=1.0.0`.

### No CLI arguments
- Dropped **`sys` / `sys.argv`** and the `python demo.py chat` branch.
- **`run_secured_agent_turn`** is now only **`(session_id, user_message)`** — no optional `model_fn` (tests use **`patch.object(demo, "deepseek_model", side_effect=demo.stub_model)`**).

### Optional chat (no argv)
- If you want the stdin loop after the printed scenarios, set **`DEMO_CHAT=1`** in the environment (or in `.env` after `load_dotenv` reloads… actually variables in `.env` are loaded at import; `DEMO_CHAT=1` in `.env` works on next run from scratch).  
- Simpler: `DEMO_CHAT=1 python3 demo.py` from the shell sets the env var for that process.

Install and test:

```bash
pip install -r requirements.txt
python3 -m unittest test_security -v
```

---

**User**

Fix this:
  @/Users/carsonching/.cursor/projects/Users-carsonching-Documents-Courses-IIMT-3688-Assignments-Integration/terminals/6.txt:102-104 


---

**Cursor**

Fixing SSL verification by using certifi's CA bundle for HTTPS requests (common on macOS Python).



Fixing two issues: restoring the full chat-completions URL (currently only the host) and supplying an SSL context using certifi's CA bundle to resolve certificate verification on macOS.



Here is what was wrong and what we changed.

### Cause
Python on macOS often fails **`CERTIFICATE_VERIFY_FAILED`** because it does not use a complete CA bundle for `urllib`. Your `DEEPSEEK_URL` was also only the host (`https://api.deepseek.com`) instead of the **chat completions** path.

### Fix
1. **`certifi`** — build an SSL context with `ssl.create_default_context(cafile=certifi.where())` and pass it as **`context=_ssl_ctx`** to `urllib.request.urlopen(...)`.
2. **URL** — set to `https://api.deepseek.com/chat/completions`.
3. **`requirements.txt`** — add `certifi>=2024.0.0`.

Reinstall deps, then run the demo again:

```bash
pip install -r requirements.txt
python3 demo.py
```

If verification still fails (corporate TLS inspection, etc.), the next step is to trust that proxy’s root cert in the system keychain or point `SSL_CERT_FILE` at your org’s CA bundle—not by turning off verification in code.

---

**User**

the program spent too much time when testing rate limit.

---

**Cursor**

Checking `demo.py`: the rate-limit demo likely runs ten full agent turns, each calling the DeepSeek API.



Using the stub model during the burst loop: each `run_secured_agent_turn` was calling `deepseek_model` up to ten times (full HTTP round-trips). Swapping to `stub_model` for that loop only keeps the rate-limit demo fast while preserving real API behavior for the valid-request case.



Here is what was going on.

**Cause:** In `__main__`, the rate-limit demo called `run_secured_agent_turn` **10 times** in a row. Each successful turn runs **`deepseek_model`**, so with a key set you were doing **10 full DeepSeek HTTP calls** before the 11th (blocked) attempt.

**Change:** For that burst block only, the module temporarily sets **`deepseek_model` to `stub_model`** inside a `try` / `finally`, then restores the real function. The limiter, validator, and ethical checks still run on every turn; only the model step is stubbed so the demo stays quick.

The **“Valid request”** case still uses the real API when `DEEPSEEK_API_KEY` is set. **“Flagged phrase”** still uses the real `deepseek_model` after restore, but it fails at ethics before any API call anyway.

---

**User**

now create: 
README.md - Security documentation (1-2 pages):
• Short system overview (problem, workflow, key components)
• Threat model
• Security measures implemented
• How to use the security module
• Limitations
Document your security measures: - What threats are addressed - How each
measure works - Limitations and future improvements


---

**Cursor**

Reviewing the implementation so README.md matches the code.



Added [`README.md`](README.md) with:

1. **System overview** — problem, ordered workflow (rate → validate → ethics in → model → ethics out), table of main pieces (`InputValidator`, `RateLimiter`, `EthicalGuard`, `run_secured_agent_turn`).
2. **Threat model** — untrusted client, abuse, prompt integrity, policy/safety, output risk, and explicit non-goals (auth, full TLS story, etc.).
3. **Security measures** — for each layer: **threats addressed**, **how it works**, plus integration/TLS/dotenv for `demo.py`.
4. **How to use** — `pip install -r requirements.txt`, `.env` / `DEEPSEEK_API_KEY`, `DEMO_CHAT`, direct class usage sample, `run_secured_agent_turn`, and `python3 -m unittest test_security -v`.
5. **Limitations and future improvements** — table (in-memory limiter, bypassable filters, sanitization scope, logging/PII, auth, model errors).

Length is roughly one to two pages when rendered. If you want it shorter or more formal for submission, say how you’d like it trimmed.

---

**User**

delete everything related to requirements.txt

---

**Cursor**

Here is what was done:

- **`requirements.txt`** — It is not in the project anymore (there was nothing to delete on disk).
- **`README.md`** — Removed the `pip install -r requirements.txt` step and replaced it with an explicit install line: `pip install python-dotenv certifi`.

There are no remaining references to `requirements.txt` under the Integration assignment folder.

