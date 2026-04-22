"""Guardrails for agent calls: validation/sanitization, rate limits, ethical screen.

Threats: abuse (RateLimiter), oversized/malformed input (InputValidator), policy
violations (EthicalGuard), plus WARNING logs with short excerpts on flags.

Flow: rate limit -> validate/sanitize -> ethics on input -> model -> ethics on output.
Limits: in-memory limiter; keyword filters are bypassable; sanitization is not full
HTML safety; log excerpts may still hold sensitive text. Production: Redis limits,
provider moderation, HTML sanitizer, log redaction.
"""

import logging
import re
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

_DEFAULT_ETHICAL_PATTERNS = [
    "ignore all previous instructions",
    "ignore previous instructions",
    "bypass safety",
    "jailbreak the model",
    "harm someone",
    "how to make a bomb",
]


class InputValidator:
    _tag_re = re.compile(r"<[^>]{0,200}?>")

    def __init__(self, max_length=1000):
        self.max_length = max_length

    def sanitize(self, text):
        text = text.replace("\x00", "")
        text = "".join(
            c for c in text if c in "\n\t\r" or ord(c) >= 32
        )
        text = text.strip()
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        text = self._tag_re.sub("", text)
        return text

    def validate(self, input_text):
        if not isinstance(input_text, str):
            return False, "Input must be a string"
        cleaned = self.sanitize(input_text)
        if not cleaned:
            return False, "Input cannot be empty"
        if len(cleaned) > self.max_length:
            return False, "Input exceeds %d characters" % self.max_length
        return True, cleaned


class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = defaultdict(list)

    def check(self, key):
        now = time.time()
        start = now - self.window_seconds
        history = self._hits[key]
        history[:] = [t for t in history if t >= start]
        if len(history) >= self.max_requests:
            return (
                False,
                "Rate limit exceeded: at most %d requests per %d seconds"
                % (self.max_requests, self.window_seconds),
            )
        history.append(now)
        return True, "OK"


class EthicalGuard:
    def __init__(self, patterns=None):
        raw = patterns if patterns is not None else _DEFAULT_ETHICAL_PATTERNS
        self._patterns = [re.compile(re.escape(p), re.IGNORECASE) for p in raw]

    def screen(self, text, context="user_input"):
        excerpt = (text[:120] + "…") if len(text) > 120 else text
        for pat in self._patterns:
            if pat.search(text):
                logger.warning(
                    "EthicalGuard flagged content context=%s excerpt=%r",
                    context,
                    excerpt,
                )
                return (
                    False,
                    "This request cannot be processed due to content policy. "
                    "Please rephrase your question.",
                )
        return True, "OK"
